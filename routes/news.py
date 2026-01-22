"""Routes for ingesting news and social posts.

Exposes a POST `/news` endpoint that accepts news articles or reddit posts
for a given company and persists them (with embeddings and sentiment)
into the `news` collection.
"""

from flask import request, jsonify, Blueprint, current_app
from sentence_transformers import SentenceTransformer
from pymongo import errors
from db.news_queries import create_news
from utils.logger import get_logger
from utils.sentiment import finbert_sentiment
from utils.embeddings import get_embeddings
from datetime import datetime
import re

news_bp = Blueprint("news", __name__)

model = SentenceTransformer('all-MiniLM-L6-v2')
logger = get_logger(__name__)

COLLECTION_NAME = "news"

# Standardizes stock ticker format
def sanitize_ticker_name(name: str) -> str:
    """Normalize and validate a ticker string.

    Replaces any character that is not a letter, number or underscore
    with underscore and converts to upper-case. Raises ValueError for
    empty/invalid input.
    """
    # Replaces all character that is not a letter, number or underscore with _
    clean = re.sub(r"[^A-Za-z0-9_]", "_", name.upper())
    if not clean:
        raise ValueError("Invalid ticker name")
    return clean

@news_bp.route("/news", methods=["POST"])
def save_news():
    """Accept and persist news articles or reddit posts.

    Expected JSON payload shape:
    - `company`: ticker or company name
    - `articles` or `posts`: list of objects with `title`, `url`, `date`, `body`

    Returns a JSON summary with number of inserted and skipped documents.
    """

    data = request.get_json(force=True)

    if not data or "company" not in data or ("articles" not in data and "posts" not in data):
        return jsonify({"error": "Invalid payload"}), 400

    try:
        ticker_name = sanitize_ticker_name(data["company"])
    except ValueError:
        return jsonify({"error": "Invalid stock ticker"}), 400

    if "articles" in data:
        source = "news"
    else:
        source = "reddit"

    inserted = 0
    skipped = 0

    articles = data.get("articles") or data.get("posts")
    
    for article in articles:
        if not all(k in article for k in ("title", "url", "date", "body")):
            continue
        
        embedding = get_embeddings(ticker_name + " " + article["title"] + " " + article["body"] + " " + article["date"]).tolist()

        sentiment = finbert_sentiment(article["title"] + " " + article["body"])

        doc = {
            "ticker": ticker_name,
            "source": source,
            "title": article["title"],
            "url": article["url"],
            "date": article["date"],
            "body": article["body"],
            "embedding": embedding,
            "ingested_at": datetime.now(),
            "sentiment": 
                    {
                        "score": sentiment["score"],
                        "positive": sentiment["positive"],
                        "neutral": sentiment["neutral"],
                        "negative": sentiment["negative"]
                    }
        }

        try:
            create_news(doc)
            inserted += 1
        except errors.DuplicateKeyError:
            skipped += 1

    return jsonify({
        "status": "success",
        "collection": "news",
        "inserted": inserted,
        "skipped_duplicates": skipped
    })



