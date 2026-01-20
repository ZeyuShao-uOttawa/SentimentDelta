from typing import Optional, List, Dict, Any
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError
from bson import ObjectId
from datetime import datetime
from logger import get_logger
from db.client import MongoDBClient

class _NewsManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.db_client = None
            self.collection_name = "news"
            self.logger = get_logger(__name__)
            self._initialized = True
    
    def initialize(self, db_client: MongoDBClient, collection_name: str = "news"):
        self.db_client = db_client
        self.collection_name = collection_name
        self.logger.info(f"NewsManager initialized with collection: {collection_name}")

    @property
    def collection(self):
        """Get the MongoDB collection."""
        if self.db_client is None or self.db_client.db is None:
            raise Exception("Database not connected. Call initialize() and ensure DB is connected.")
        return self.db_client.db[self.collection_name]

    def create_one(self, doc: Dict[str, Any]) -> ObjectId:
        result = self.collection.insert_one(doc)
        return result.inserted_id

    def create_many(self, docs: List[Dict[str, Any]]) -> int:
        if not docs:
            return 0
        try:
            result = self.collection.insert_many(docs, ordered=False)
            return len(result.inserted_ids)
        except BulkWriteError as e:
            return e.details['nInserted']

    def find_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return self.collection.find_one({"_id": ObjectId(doc_id)})

    def find_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        return list(self.collection.find().limit(limit))

    def find_by_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        return list(
            self.collection.find({"ticker": ticker})
        )

    def find_by_ticker_and_date(self, ticker: str, date_str: str, projection: Optional[Dict[str, int]] = None) -> List[Dict[str, Any]]:
        """
        date_str format: YYYY-MM-DD
        Optional `projection` dict to limit returned fields.
        """
        query = {
            "ticker": ticker,
            "date": date_str
        }
        if projection:
            return list(self.collection.find(query, projection))
        return list(self.collection.find(query))
    
    def get_news_all_dates(self, ticker: Optional[str] = None) -> List[str]:
        """
        Get all unique dates for news articles.
        
        Args:
            ticker (str, optional): If provided, filter by ticker.
        
        Returns:
            List of unique date strings (YYYY-MM-DD), sorted ascending.
        """
        query = {"ticker": ticker} if ticker else {}
        dates = self.collection.distinct("date", filter=query)
        return sorted(dates)

    def find_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Find a news article by URL."""
        return self.collection.find_one({"url": url})

    def find_date_range(self, ticker: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Uses string comparison safely because format is YYYY-MM-DD
        """
        return list(
            self.collection.find({
                "ticker": ticker,
                "date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }).sort("date", 1)
        )

    def find_latest_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Find the latest news article for a ticker based on date and ingested_at."""
        try:
            query = {"ticker": ticker}
            # Sort by date descending, then by ingested_at descending
            result = self.collection.find(query).sort([("date", -1), ("ingested_at", -1)]).limit(1)
            
            latest = list(result)
            if latest:
                self.logger.info(f"Found latest news for ticker {ticker}")
                return latest[0]
            else:
                self.logger.info(f"No news found for ticker {ticker}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error reading latest news for ticker {ticker}: {e}")
            return None

    def avg_sentiment_by_day(self, ticker: str, date_str: str) -> Dict[str, float] | None:
        pipeline = [
            {"$match": {"ticker": ticker, "date": date_str}},
            {"$group": {
                "_id": None,
                "score": {"$avg": "$sentiment.score"},
                "positive": {"$avg": "$sentiment.positive"},
                "neutral": {"$avg": "$sentiment.neutral"},
                "negative": {"$avg": "$sentiment.negative"},
            }},
        ]

        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else None
    
    def update_by_id(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": updates}
        )
        return result.matched_count == 1

    def update_sentiment(self, doc_id: str, sentiment: Dict[str, float]) -> bool:
        return self.update_by_id(
            doc_id,
            {"sentiment": sentiment}
        )

    def update_embedding(self, doc_id: str, embedding: List[float]) -> bool:
        return self.update_by_id(
            doc_id,
            {"embedding": embedding}
        )
    
    def delete_by_id(self, doc_id: str) -> bool:
        result = self.collection.delete_one(
            {"_id": ObjectId(doc_id)}
        )
        return result.deleted_count == 1

    def delete_by_ticker(self, ticker: str) -> int:
        result = self.collection.delete_many(
            {"ticker": ticker}
        )
        return result.deleted_count

# Global singleton instance
_news_manager = _NewsManager()

# Module-level functions that use the singleton
def initialize_news_manager(db, collection_name: str = "news"):
    """Initialize the global news manager."""
    _news_manager.initialize(db, collection_name)

def create_news(doc: Dict[str, Any]) -> ObjectId:
    return _news_manager.create_one(doc)

def create_many_news(docs: List[Dict[str, Any]]) -> int:
    return _news_manager.create_many(docs)

def get_news_by_id(doc_id: str) -> Optional[Dict[str, Any]]:
    return _news_manager.find_by_id(doc_id)

def get_all_news(limit: int = 100) -> List[Dict[str, Any]]:
    return _news_manager.find_all(limit)

def get_news_by_ticker(ticker: str) -> List[Dict[str, Any]]:
    return _news_manager.find_by_ticker(ticker)

def get_news_by_ticker_and_date(ticker: str, date_str: str, projection: Optional[Dict[str, int]] = None) -> List[Dict[str, Any]]:
    return _news_manager.find_by_ticker_and_date(ticker, date_str, projection)

def get_news_date_range(ticker: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    return _news_manager.find_date_range(ticker, start_date, end_date)

def get_latest_news_by_ticker(ticker: str) -> Optional[Dict[str, Any]]:
    return _news_manager.find_latest_by_ticker(ticker)

def get_news_by_url(url: str) -> Optional[Dict[str, Any]]:
    return _news_manager.find_by_url(url)

def get_avg_sentiment(ticker: str, date_str: str) -> Optional[Dict[str, float]]:
    return _news_manager.avg_sentiment_by_day(ticker, date_str)

def update_news(doc_id: str, updates: Dict[str, Any]) -> bool:
    return _news_manager.update_by_id(doc_id, updates)

def update_news_sentiment(doc_id: str, sentiment: Dict[str, float]) -> bool:
    return _news_manager.update_sentiment(doc_id, sentiment)

def update_news_embedding(doc_id: str, embedding: List[float]) -> bool:
    return _news_manager.update_embedding(doc_id, embedding)

def delete_news(doc_id: str) -> bool:
    return _news_manager.delete_by_id(doc_id)

def delete_news_by_ticker(ticker: str) -> int:
    return _news_manager.delete_by_ticker(ticker)

def get_news_dates(ticker: Optional[str] = None) -> List[str]:
    """
    Get all unique news dates. Optionally filter by ticker.
    """
    return _news_manager.get_news_all_dates(ticker)