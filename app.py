from flask import Flask, request, jsonify
from flask_cors import CORS
from newspaper import Article
from readability import Document
from bs4 import BeautifulSoup
import requests
import os

app = Flask(__name__)
CORS(app)


def extract_with_newspaper(url: str):
    article = Article(url)
    article.download()
    article.parse()

    content = article.text.strip()
    if len(content.split()) < 300:
        return None

    publish_date = None
    if article.publish_date:
        publish_date = article.publish_date.isoformat()

    return {
        "original_title": article.title,
        "original_article": content,
        "authors": article.authors,
        "publish_date": publish_date,
        "top_image": article.top_image,
        "word_count": len(content.split()),
        "extraction_method": "newspaper3k"
    }


def extract_with_readability(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)

    doc = Document(response.text)
    html = doc.summary()

    soup = BeautifulSoup(html, "html.parser")
    paragraphs = soup.find_all("p")
    content = "\n\n".join(p.get_text(strip=True) for p in paragraphs)

    if len(content.split()) < 300:
        return None

    return {
        "original_title": doc.title(),
        "original_article": content,
        "authors": [],
        "publish_date": None,
        "top_image": None,
        "word_count": len(content.split()),
        "extraction_method": "readability"
    }


def extract_generic(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)

    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = soup.find_all("p")
    content = "\n\n".join(p.get_text(strip=True) for p in paragraphs)

    title = soup.title.string if soup.title else ""

    return {
        "original_title": title,
        "original_article": content,
        "authors": [],
        "publish_date": None,
        "top_image": None,
        "word_count": len(content.split()),
        "extraction_method": "generic_dom"
    }


def fetch_article(url: str):
    # Strategy 1: newspaper3k
    try:
        result = extract_with_newspaper(url)
        if result:
            return result
    except Exception:
        pass

    # Strategy 2: Readability
    try:
        result = extract_with_readability(url)
        if result:
            return result
    except Exception:
        pass

    # Strategy 3: Generic fallback
    return extract_generic(url)


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
    url = (data.get("url") or "").strip()

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