from typing import Optional, List, Dict, Any
from pymongo.collection import Collection
from bson import ObjectId
from datetime import datetime

class NewsRepository:
    def __init__(self, db):
        self.collection: Collection = db["news"]

    def create_one(self, doc: Dict[str, Any]) -> ObjectId:
        result = self.collection.insert_one(doc)
        return result.inserted_id

    def create_many(self, docs: List[Dict[str, Any]]) -> List[ObjectId]:
        if not docs:
            return []
        result = self.collection.insert_many(docs, ordered=False)
        return result.inserted_ids

    def find_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return self.collection.find_one({"_id": ObjectId(doc_id)})

    def find_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        return list(self.collection.find().limit(limit))

    def find_by_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        return list(
            self.collection.find({"ticker": ticker})
        )

    def find_by_ticker_and_date(self, ticker: str, date_str: str) -> List[Dict[str, Any]]:
        """
        date_str format: YYYY-MM-DD
        """
        return list(
            self.collection.find({
                "ticker": ticker,
                "date": date_str
            })
        )

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