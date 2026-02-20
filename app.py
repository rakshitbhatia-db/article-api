from flask import Flask, request, jsonify
from flask_cors import CORS
from newspaper import Article
import os

app = Flask(__name__)
CORS(app)


def fetch_article(url: str) -> dict:
    article = Article(url)
    article.download()
    article.parse()

    # Try to extract metadata
    publish_date = None
    if article.publish_date:
        publish_date = article.publish_date.isoformat()

    return {
        "original_title": article.title,
        "original_article": article.text,
        "authors": article.authors,
        "publish_date": publish_date,
        "top_image": article.top_image,
        "word_count": len(article.text.split())
    }


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def home():
    return {"status": "Article API live", "endpoints": ["/health", "/fetch"]}


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