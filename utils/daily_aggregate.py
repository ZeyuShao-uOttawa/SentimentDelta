from pymongo import MongoClient
from datetime import datetime
from collections import Counter
import math
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI_MEET", "mongodb://mongo:27017")
DB_NAME = "stock_market_db"
COLLECTION_NAME = "news"

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def retrieve_daily_news(search_date, ticker):
    # Specify which fields you want returned (Only need sentiment)
    projection = {
        "_id": 0,
        "sentiment": 1
    }

    query = {
        "date": search_date,
        "ticker": ticker
    }

    docs = list(collection.find(query, projection))
    
    if docs:
        for doc in docs:
            print(doc)
    else:
        print("No documents found for", ticker, "on", search_date)
    
    return docs

def all_scores(docs):
    return [d["sentiment_score"] for d in docs]


# Average sentiment score (High = Bullish | 0 = Neutral | Low = Bearish)
def sentiment_mean(docs):
    scores = all_scores(docs)

    sent_mean = np.mean(scores) if scores else 0.0

    return sent_mean

# Standard deviation of scores (High = Agreement | Low = Disagreement)
def sentiment_std(docs):
    scores = all_scores(docs)

    sent_std = np.std(scores) if len(scores) > 1 else 0.0

    return sent_std

# Attention count of total articles (High = Consensus Has Weight | Low = Consensus Might Not Matter)
def sentiment_attention(docs):
    att = len(docs)

    return att

def sentiment_bear_bull_ratio(docs):
    bullish = sum(1 for d in docs if d["sentiment_score"] > 0)
    bearish = sum(1 for d in docs if d["sentiment_score"] < 0)

    bear_bull_ratio = bullish / (bearish + 1)

    return bear_bull_ratio

def daily_aggregate(search_date, ticker):
    docs = retrieve_daily_news(search_date, ticker)

    sent_mean = sentiment_mean(docs)
    sent_std = sentiment_mean(docs)
    att = sentiment_attention(docs)
    bear_bull_ratio = sentiment_bear_bull_ratio(docs)

    features = {
        "sent_mean": sent_mean,
        "sent_std": sent_std,
        "attention": att,
        "bear_bull_ratio": bear_bull_ratio
    }

if __name__ == "__main__":
    search_date = "2026-01-11"
    ticker = "AAPL"

    retrieve_daily_news(search_date, ticker)