from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import trafilatura

app = Flask(__name__)
CORS(app)

WEBSCRAPING_ENDPOINT = "https://api.webscrapingapi.com/v2"
API_KEY = "AeJXjrVSxOlt6Oc0to63Ok4DK2AQrlPy"


def fetch_html_via_webscrapingapi(url: str) -> str:
    if not API_KEY:
        raise Exception("Missing WEBSCRAPINGAPI_KEY environment variable")

    params = {
        "api_key": API_KEY,
        "url": url,
        "render_js": "1"
    }

    response = requests.get(WEBSCRAPING_ENDPOINT, params=params, timeout=60)
    response.raise_for_status()
    return response.text


def extract_article_from_html(html: str):
    extracted_text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        favor_recall=True
    )

    if not extracted_text:
        return None

    metadata = trafilatura.extract_metadata(html)

    return {
        "original_title": metadata.title if metadata else "",
        "original_article": extracted_text,
        "authors": metadata.author if metadata and metadata.author else "",
        "publish_date": metadata.date if metadata and metadata.date else "",
        "top_image": metadata.image if metadata and metadata.image else "",
        "word_count": len(extracted_text.split()),
        "extraction_method": "webscrapingapi_trafilatura"
    }


def fetch_article(url: str):
    html = fetch_html_via_webscrapingapi(url)
    result = extract_article_from_html(html)

    if not result:
        raise Exception("Article extraction failed")

    return result


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def home():
    return {
        "status": "Article API live",
        "endpoints": ["/health", "/fetch"]
    }


@app.post("/fetch")
def fetch():
    data = request.get_json(silent=True) or {}

    url = (
        data.get("url")
        or data.get("URL")
        or data.get("link")
        or request.form.get("url")
        or request.args.get("url")
        or ""
    ).strip()

    if not url:
        return jsonify({
            "status": "error",
            "message": "Missing 'url' in JSON body"
        }), 400

    try:
        result = fetch_article(url)

        if not result["original_article"]:
            return jsonify({
                "status": "error",
                "message": "Extraction failed or empty content"
            }), 500

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)