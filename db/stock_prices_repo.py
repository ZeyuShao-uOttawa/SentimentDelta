from typing import List, Dict, Any, Optional
from pymongo.collection import Collection
from datetime import datetime

class StocksRepository:
    def __init__(self, db):
        self.collection: Collection = db["stock_prices"]

    def create_one(self, doc: Dict[str, Any]) -> str:
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)

    def create_many(self, docs: List[Dict[str, Any]]) -> int:
        if not docs:
            return 0
        result = self.collection.insert_many(docs, ordered=False)
        return len(result.inserted_ids)

    def find_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return self.collection.find_one({"_id": doc_id})

    def find_by_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        return list(
            self.collection.find(
                {"Ticker": ticker}
            ).sort("Datetime", 1)
        )

    def find_by_ticker_and_datetime(self, ticker: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        return list(
            self.collection.find({
                "Ticker": ticker,
                "Datetime": {
                    "$gte": start,
                    "$lte": end
                }
            }).sort("Datetime", 1)
        )

    def find_latest_stock_data(self, ticker: str) -> Dict[str, Any] | None:
        return self.collection.find_one(
            {"Ticker": ticker},
            sort=[("Datetime", -1)]
        )
    
    def update_by_id(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        result = self.collection.update_one(
            {"_id": doc_id},
            {"$set": updates}
        )
        return result.matched_count == 1

    def upsert_price(self, doc_id: str, doc: Dict[str, Any]) -> None:
        self.collection.update_one(
            {"_id": doc_id},
            {"$set": doc},
            upsert=True
        )

    def delete_by_id(self, doc_id: str) -> bool:
        result = self.collection.delete_one(
            {"_id": doc_id}
        )
        return result.deleted_count == 1

    def delete_by_ticker(self, ticker: str) -> int:
        result = self.collection.delete_many(
            {"Ticker": ticker}
        )
        return result.deleted_count