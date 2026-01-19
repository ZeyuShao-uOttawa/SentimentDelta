from pymongo import MongoClient
from utils.sentiment import finbert_sentiment
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI_MEET", "mongodb://mongo:27017")
DB_NAME = "stock_market_db"
COLLECTION_NAME = "news"

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def update_news_with_sentiment():
    """
    Function to update all documents in the news collection with a sentiment score
    """
    for doc in collection.find({}):
        sentiment = finbert_sentiment(doc.get("title") + " " + doc.get("body"))

        collection.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "sentiment": 
                    {
                        "score": sentiment["score"],
                        "positive": sentiment["positive"],
                        "neutral": sentiment["neutral"],
                        "negative": sentiment["negative"]
                    }
                }
            }
        )

    print("All documents updated")

if __name__ == "__main__":
    update_news_with_sentiment()