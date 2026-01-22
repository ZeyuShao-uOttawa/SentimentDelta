"""Routes for ingesting news and social posts.

Exposes a POST `/news` endpoint that accepts news articles or reddit posts
for a given company and persists them (with embeddings and sentiment)
into the `news` collection.
"""

from flask import request, jsonify, Blueprint, current_app
from sentence_transformers import SentenceTransformer
from pymongo import errors
from db.news_queries import (
    create_news,
    get_all_news,
    get_news_by_ticker,
    get_news_by_ticker_and_date,
    get_news_date_range,
    get_news_summary,
)
from utils.logger import get_logger
from utils.sentiment import finbert_sentiment
from utils.embeddings import get_embeddings
from datetime import datetime
import re
from typing import List, Dict, Any
from bson import ObjectId

news_bp = Blueprint("news", __name__)

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


def _serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert DB document fields to JSON serializable types."""
    out = {}
    for k, v in doc.items():
        if k == "_id":
            out[k] = str(v)
            continue
        if isinstance(v, datetime):
            out[k] = v.isoformat()
            continue
        try:
            if isinstance(v, ObjectId):
                out[k] = str(v)
                continue
        except Exception:
            pass
        out[k] = v
    return out

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


@news_bp.route("/news/list", methods=["GET"])
def list_all_news():
    """Return all news with optional `limit` query param."""
    limit = request.args.get("limit")
    try:
        limit_val = int(limit) if limit else 100
    except ValueError:
        return jsonify({"error": "invalid limit"}), 400

    docs = get_all_news(limit_val)
    return jsonify({"count": len(docs), "data": [_serialize_doc(d) for d in docs]}), 200


@news_bp.route("/news/ticker/<ticker>/list", methods=["GET"])
def list_news_by_ticker(ticker: str):
    """Return news for a ticker with optional `limit` query param."""
    limit = request.args.get("limit")
    try:
        limit_val = int(limit) if limit else 100
    except ValueError:
        return jsonify({"error": "invalid limit"}), 400

    docs = get_news_by_ticker(ticker.upper(), limit_val)
    return jsonify({"ticker": ticker.upper(), "count": len(docs), "data": [_serialize_doc(d) for d in docs]}), 200


@news_bp.route("/news/ticker/<ticker>/date/<date_str>", methods=["GET"])
def news_by_ticker_and_date(ticker: str, date_str: str):
    """Return news for a ticker on a specific date. Optional `projection` query param (comma-separated fields)."""
    proj_param = request.args.get("projection")
    projection = None
    if proj_param:
        fields = [f.strip() for f in proj_param.split(",") if f.strip()]
        projection = {f: 1 for f in fields}

    docs = get_news_by_ticker_and_date(ticker.upper(), date_str, projection)
    return jsonify({"ticker": ticker.upper(), "date": date_str, "count": len(docs), "data": [_serialize_doc(d) for d in docs]}), 200


@news_bp.route("/news/ticker/<ticker>/range", methods=["GET"])
def news_by_ticker_range(ticker: str):
    """Return news for a ticker between `start` and `end` query params (YYYY-MM-DD)."""
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        return jsonify({"error": "start and end required"}), 400

    docs = get_news_date_range(ticker.upper(), start, end)
    return jsonify({"ticker": ticker.upper(), "start": start, "end": end, "count": len(docs), "data": [_serialize_doc(d) for d in docs]}), 200


@news_bp.route("/news/summary", methods=["GET"])
def news_summary():
    """Return a summary for `ticker` including counts, averages and latest doc."""
    summary = get_news_summary()
    if not summary:
        return jsonify({"error": "not_found"}), 404
    if "latest" in summary and isinstance(summary["latest"], dict):
        summary["latest"] = _serialize_doc(summary["latest"])
    return jsonify(summary), 200


