import requests
from pymongo import MongoClient, errors
from datetime import datetime, timezone
from config.config import ApiConfig

from utils.sentiment import finbert_sentiment
from utils.embeddings import setup_embeddings, get_embeddings

# Configuration
FINNHUB_API_KEY = ApiConfig.FINNHUB_API_KEY
MONGO_URI = ApiConfig.MONGODB_URI
DB_NAME = ApiConfig.MONGO_DB
COLLECTION_NAME = "news"
FIELDS_TO_REMOVE = [
    "category",
    "id",
    "image"
]
RENAME_MAP = {
    "headline": "title",
    "datetime": "date",
    "related": "ticker",
    "summary": "body"
}

setup_embeddings(ApiConfig.EMBEDDING_MODEL)

def retrieve_and_store_news(symbol: str, from_date: str, to_date: str):
    """
    Retrieve news from Finnhub API and store in MongoDB.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        from_date: Start date (format: YYYY-MM-DD)
        to_date: End date (format: YYYY-MM-DD)
    """
    try:
        # Fetch data from Finnhub
        url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={from_date}&to={to_date}&token={FINNHUB_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        news_data = response.json()
        
        if not news_data:
            print(f"No news found for {symbol}")
            return
        
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        inserted = 0
        skipped = 0

        # Add metadata and insert
        for article in news_data:
            for field in FIELDS_TO_REMOVE:
                article.pop(field, None)
            
            for old_key, new_key in RENAME_MAP.items():
                if old_key in article:
                    article[new_key] = article.pop(old_key)

            article["date"] = datetime.fromtimestamp(article["date"], tz=timezone.utc).strftime("%Y-%m-%d")
            article["ingested_at"] = datetime.now()

            embedding = get_embeddings(article["ticker"] + " " + article["title"] + " " + article["body"] + " " + article["date"]).tolist()
            sentiment = finbert_sentiment(article["title"] + " " + article["body"])

            article["embedding"] = embedding
            article["sentiment"] = {
                "score": sentiment["score"],
                "positive": sentiment["positive"],
                "neutral": sentiment["neutral"],
                "negative": sentiment["negative"]
            }

            try:
                collection.insert_one(article)
                inserted += 1
            except errors.DuplicateKeyError:
                skipped += 1

        print(f"Successfully stored {inserted} articles for {symbol}, skipped {skipped}")
        
        client.close()
    
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    for symbol in ApiConfig.TICKERS:
        retrieve_and_store_news(symbol, "2025-01-01", "2025-12-31")