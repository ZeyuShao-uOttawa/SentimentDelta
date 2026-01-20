from pymongo import MongoClient
from datetime import datetime, timedelta
from utils.sentiment import finbert_sentiment
from utils.daily_aggregate  import daily_aggregate
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI_MEET", "mongodb://mongo:27017")
DB_NAME = "stock_market_db"
COLLECTION_NAME = "news"
TARGET_COLLECTION_NAME = "aggregates"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
target_collection = db[TARGET_COLLECTION_NAME]

def calculate_aggregate(search_date, ticker):
    """
    Function to update all documents in the news collection with a sentiment score
    """
    projection = {
        "_id": 0,
        "sentiment": 1
    }

    query = {
        "date": search_date.strftime("%Y-%m-%d"),
        "ticker": ticker
    }

    docs = list(collection.find(query, projection))

    if docs:
        features = daily_aggregate(docs)
        features["date"] = search_date.strftime("%Y-%m-%d")
        features["ticker"] = ticker

        print(features)

        target_collection.insert_one(features)
    else:
        print("No documents found for", ticker, "on", search_date)

if __name__ == "__main__":
    TICKERS = ["AMZN", "GOOGL", "META", "MSFT", "NFLX", "NVDA", "TSLA"]
    start_str = "2026-01-01"
    end_str = "2026-01-19"

    start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_str, "%Y-%m-%d").date()

    current_date = start_date
    while current_date <= end_date:
        for ticker in TICKERS:
            print(current_date.strftime("%Y-%m-%d"))
            calculate_aggregate(current_date, ticker)

        current_date += timedelta(days=1)