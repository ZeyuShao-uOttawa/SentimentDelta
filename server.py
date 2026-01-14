from flask import Flask, request, jsonify, Blueprint
from pymongo import MongoClient, errors
from sentence_transformers import SentenceTransformer
from datetime import datetime
from utils.sentiment import finbert_sentiment
import os
import re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
api = Blueprint("api", __name__, url_prefix="/api/v1")

MONGO_URI = os.getenv("MONGO_URI_MEET", "mongodb://mongo:27017")
client = MongoClient(MONGO_URI)
stock_market_db = client.stock_market_db
model = SentenceTransformer('all-MiniLM-L6-v2')

# Standardizes stock ticker format
def sanitize_ticker_name(name: str) -> str:
    # Replaces all character that is not a letter, number or underscore with _
    clean = re.sub(r"[^A-Za-z0-9_]", "_", name.upper())
    if not clean:
        raise ValueError("Invalid ticker name")
    return clean

def create_embedding(text):
    embedding = model.encode(text)
    return embedding.tolist()

@api.route("/news", methods=["POST"])
def save_news():
    data = request.get_json(force=True)

    if not data or "company" not in data or ("articles" not in data and "posts" not in data):
        return jsonify({"error": "Invalid payload"}), 400

    try:
        ticker_name = sanitize_ticker_name(data["company"])
    except ValueError:
        return jsonify({"error": "Invalid stock ticker"}), 400

    collection = stock_market_db["news"]

    if "articles" in data:
        source = "news"
    else:
        source = "reddit"

    # Prevent duplicates by URL (Mongo will not create a new index if it already exists on collection)
    collection.create_index("url", unique=True)

    inserted = 0
    skipped = 0

    articles = data.get("articles") or data.get("posts")

    for article in articles:
        if not all(k in article for k in ("title", "url", "date", "body")):
            continue
        
        embedding = create_embedding(ticker_name + " " + article["title"] + " " + article["body"] + " " + article["date"])

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
            collection.insert_one(doc)
            inserted += 1
        except errors.DuplicateKeyError:
            skipped += 1

    return jsonify({
        "status": "success",
        "collection": "news",
        "inserted": inserted,
        "skipped_duplicates": skipped
    })

app.register_blueprint(api)

if __name__ == "__main__":
    app.run(port=5000, debug=True)