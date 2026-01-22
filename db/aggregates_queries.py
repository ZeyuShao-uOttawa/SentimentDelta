
from typing import Optional, List, Dict, Any
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError
from bson import ObjectId
from datetime import datetime
from logger import get_logger
from db.client import MongoDBClient


class _AggregatesManager:
	_instance = None
	_initialized = False

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
		return cls._instance

	def __init__(self):
		if not self._initialized:
			self.db_client = None
			self.collection_name = "aggregates"
			self.logger = get_logger(__name__)
			self._initialized = True
    
	def initialize(self, db_client: MongoDBClient, collection_name: str = "aggregates"):
		self.db_client = db_client
		self.collection_name = collection_name
		self.logger.info(f"AggregatesManager initialized with collection: {collection_name}")

	@property
	def collection(self):
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
			return e.details.get('nInserted', 0)

	def find_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
		return self.collection.find_one({"_id": ObjectId(doc_id)})

	def find_all(self, limit: int = 100) -> List[Dict[str, Any]]:
		return list(self.collection.find().limit(limit))

	def find_by_ticker(self, ticker: str) -> List[Dict[str, Any]]:
		return list(self.collection.find({"ticker": ticker}))

	def find_by_ticker_and_date(self, ticker: str, date_str: str) -> List[Dict[str, Any]]:
		return list(self.collection.find({"ticker": ticker, "date": date_str}))

	def get_news_by_ticker_and_date(self, ticker: str, date_str: str, projection: Optional[Dict[str, int]] = None) -> List[Dict[str, Any]]:
		"""Read documents from the `news` collection for a given ticker and date.
		This mirrors the usage in `scripts/calculate_all_aggregates.py`.
		"""
		if self.db_client is None or self.db_client.db is None:
			raise Exception("Database not connected. Call initialize() and ensure DB is connected.")
		news_col = self.db_client.db["news"]
		query = {"ticker": ticker, "date": date_str}
		if projection:
			return list(news_col.find(query, projection))
		return list(news_col.find(query))

	def get_aggregates_all_dates(self, ticker: Optional[str] = None) -> List[str]:
		"""Get all unique dates for aggregate documents.

		Args:
			ticker (str, optional): If provided, filter by ticker.

		Returns:
			List of unique date strings (YYYY-MM-DD), sorted ascending.
		"""
		query = {"ticker": ticker} if ticker else {}
		dates = self.collection.distinct("date", filter=query)
		return sorted(dates)

	def update_by_ticker_and_date(self, ticker: str, date_str: str, updates: Dict[str, Any]) -> bool:
		result = self.collection.update_one({"ticker": ticker, "date": date_str}, {"$set": updates}, upsert=True)
		return result.matched_count == 1

	def upsert_by_ticker_and_date(self, ticker: str, date_str: str, doc: Dict[str, Any]) -> Optional[ObjectId]:
		"""Insert or update an aggregate document keyed by `ticker`+`date`. Returns the document _id."""
		result = self.collection.update_one({"ticker": ticker, "date": date_str}, {"$set": doc}, upsert=True)
		if getattr(result, "upserted_id", None):
			return result.upserted_id
		# if no upsert id, return existing _id
		existing = self.collection.find_one({"ticker": ticker, "date": date_str}, {"_id": 1})
		return existing.get("_id") if existing else None

	def find_date_range(self, ticker: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
		return list(self.collection.find({
			"ticker": ticker,
			"date": {
				"$gte": start_date,
				"$lte": end_date
			}
		}).sort("date", 1))

	def find_latest_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
		try:
			query = {"ticker": ticker}
			result = self.collection.find(query).sort([("date", -1), ("_id", -1)]).limit(1)
			latest = list(result)
			if latest:
				self.logger.info(f"Found latest aggregate for ticker {ticker}")
				return latest[0]
			else:
				self.logger.info(f"No aggregates found for ticker {ticker}")
				return None
		except Exception as e:
			self.logger.error(f"Error reading latest aggregate for ticker {ticker}: {e}")
			return None

	def update_by_id(self, doc_id: str, updates: Dict[str, Any]) -> bool:
		result = self.collection.update_one({"_id": ObjectId(doc_id)}, {"$set": updates})
		return result.matched_count == 1

	def delete_by_id(self, doc_id: str) -> bool:
		result = self.collection.delete_one({"_id": ObjectId(doc_id)})
		return result.deleted_count == 1

	def delete_by_ticker(self, ticker: str) -> int:
		result = self.collection.delete_many({"ticker": ticker})
		return result.deleted_count


# Global singleton instance
_aggregates_manager = _AggregatesManager()


# Module-level wrapper functions
def initialize_aggregates_manager(db, collection_name: str = "aggregates"):
	_aggregates_manager.initialize(db, collection_name)

def create_aggregate(doc: Dict[str, Any]) -> ObjectId:
	return _aggregates_manager.create_one(doc)

def create_many_aggregates(docs: List[Dict[str, Any]]) -> int:
	return _aggregates_manager.create_many(docs)

def get_aggregate_by_id(doc_id: str) -> Optional[Dict[str, Any]]:
	return _aggregates_manager.find_by_id(doc_id)

def get_all_aggregates(limit: int = 100) -> List[Dict[str, Any]]:
	return _aggregates_manager.find_all(limit)

def get_aggregates_by_ticker(ticker: str) -> List[Dict[str, Any]]:
	return _aggregates_manager.find_by_ticker(ticker)

def get_aggregates_by_ticker_and_date(ticker: str, date_str: str) -> List[Dict[str, Any]]:
	return _aggregates_manager.find_by_ticker_and_date(ticker, date_str)

def get_aggregate_date_range(ticker: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
	return _aggregates_manager.find_date_range(ticker, start_date, end_date)

def get_latest_aggregate_by_ticker(ticker: str) -> Optional[Dict[str, Any]]:
	return _aggregates_manager.find_latest_by_ticker(ticker)

def update_aggregate(doc_id: str, updates: Dict[str, Any]) -> bool:
	return _aggregates_manager.update_by_id(doc_id, updates)

def update_aggregate_by_ticker_and_date(ticker: str, date_str: str, updates: Dict[str, Any]) -> bool:
	return _aggregates_manager.update_by_ticker_and_date(ticker, date_str, updates)

def delete_aggregate(doc_id: str) -> bool:
	return _aggregates_manager.delete_by_id(doc_id)

def delete_aggregates_by_ticker(ticker: str) -> int:
	return _aggregates_manager.delete_by_ticker(ticker)

def get_aggregate_dates(ticker: Optional[str] = None) -> List[str]:
    return _aggregates_manager.get_aggregates_all_dates(ticker)