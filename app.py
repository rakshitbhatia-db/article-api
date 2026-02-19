from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)  # allow cross-origin requests (handy for Lovable/browser calls)

from newspaper import Article

def fetch_article(url: str) -> dict:
    article = Article(url)
    article.download()
    article.parse()

    return {
        "title": article.title,
        "content": article.text
    }

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/fetch")
def fetch():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"error": "Missing 'url' in JSON body"}), 400

    try:
        result = fetch_article(url)
        return jsonify(result)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Fetch failed: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
    
@app.get("/")
def home():
    return {"message": "Article API running. Use /health or POST /fetch"}

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)