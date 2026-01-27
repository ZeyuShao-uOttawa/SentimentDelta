from pymongo import MongoClient
from utils.sentiment import finbert_sentiment
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
SOURCE_DB_NAME = "meet_data"
TARGET_DB_NAME = "stock_market_db"
SOURCE_COLLECTION_1 = "finviz_news"
SOURCE_COLLECTION_2 = "yahoo_news"
TARGET_COLLECTION = "news"
BATCH_SIZE = 500

client = MongoClient(MONGODB_URI)
source_db = client[SOURCE_DB_NAME]
target_db = client[TARGET_DB_NAME]
source_col_1 = source_db[SOURCE_COLLECTION_1]
source_col_2 = source_db[SOURCE_COLLECTION_2]
target_col = target_db[TARGET_COLLECTION]

def migrate_finviz_news_to_news_container():
    # Getting mongo cursors to limit requests size to BATCH_SIZE
    cursor_1 = source_col_1.find({}, no_cursor_timeout=True).batch_size(BATCH_SIZE)

    for doc in cursor_1:
        sentiment = finbert_sentiment(doc.get("title") + " " + doc.get("summary"))

        transformed = {
            "ticker": doc.get("ticker"),
            "source": doc.get("source"),
            "title": doc.get("title"),
            "url": doc.get("url"),
            "date": doc.get("date"),
            "body": doc.get("summary"),
            "embedding": doc.get("embedding"),
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
            target_col.insert_one(transformed)
            migrated += 1
        except Exception:
            skipped += 1

def migrate_yahoo_news_to_news_container():
    cursor_2 = source_col_2.find({}, no_cursor_timeout=True).batch_size(BATCH_SIZE)

    for doc in cursor_2:
        sentiment = finbert_sentiment(doc.get("title") + " " + doc.get("body"))

        transformed = {
            "ticker": doc.get("ticker"),
            "source": doc.get("source"),
            "title": doc.get("title"),
            "url": doc.get("url"),
            "date": doc.get("date"),
            "body": doc.get("body"),
            "embedding": doc.get("embedding"),
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
            target_col.insert_one(transformed)
            migrated += 1
        except Exception:
            skipped += 1

if __name__ == "__main__":
    migrate_finviz_news_to_news_container()
    migrate_yahoo_news_to_news_container()