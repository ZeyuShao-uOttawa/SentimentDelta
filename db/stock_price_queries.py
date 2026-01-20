"""Stock price CRUD operations with singleton pattern."""

from typing import List, Dict, Any, Optional
from pymongo import errors, UpdateOne
from logger import get_logger
from datetime import datetime, timezone
import pandas as pd
from db.client import MongoDBClient

logger = get_logger(__name__)

class StockPriceManager:
    """Singleton manager for stock price CRUD operations."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.db_manager = None
            self.collection_name = "stock_prices"
            self._initialized = True
    
    def initialize(self, db_manager: MongoDBClient, collection_name: str = "stock_prices"):
        """Initialize the manager with database connection."""
        self.db_manager = db_manager
        self.collection_name = collection_name
        logger.info(f"StockPriceManager initialized with collection: {collection_name}")
    
    @property
    def collection(self):
        """Get the MongoDB collection."""
        if self.db_manager is None or self.db_manager.db is None:
            raise Exception("Database not connected. Call initialize() and ensure DB is connected.")
        return self.db_manager.db[self.collection_name]
    
    def create(self, stock_data: Dict[str, Any]) -> bool:
        """Create a single stock price record."""
        try:
            # Ensure datetime is properly formatted
            if 'Datetime' in stock_data and isinstance(stock_data['Datetime'], str):
                stock_data['Datetime'] = pd.to_datetime(stock_data['Datetime'])
            
            # Use id as _id if present
            if 'id' in stock_data:
                stock_data['_id'] = stock_data.pop('id')
            
            result = self.collection.insert_one(stock_data)
            logger.info(f"Inserted stock data with ID: {result.inserted_id}")
            return True
        except errors.DuplicateKeyError:
            logger.warning(f"Duplicate key error for stock data: {stock_data.get('_id', 'Unknown')}")
            return False
        except Exception as e:
            logger.error(f"Error inserting stock data: {e}")
            return False
    
    def create_many(self, stock_data_list: List[Dict[str, Any]], batch_size: int = 1000) -> int:
        """Create multiple stock price records in batches with upsert to handle duplicates."""
        if not stock_data_list:
            return 0
        
        total_upserted = 0
        try:
            # Process datetime fields
            for data in stock_data_list:
                if 'Datetime' in data and isinstance(data['Datetime'], str):
                    data['Datetime'] = pd.to_datetime(data['Datetime'])
            
            # Insert in batches using upsert to prevent duplicates
            for i in range(0, len(stock_data_list), batch_size):
                batch = stock_data_list[i:i + batch_size]
                
                # Use bulk upsert operations to handle duplicates
                bulk_ops = []
                for doc in batch:
                    if 'id' in doc:
                        # Use the id as _id and remove the separate id field
                        doc_id = doc.pop('id')  # Remove 'id' and use its value as _id
                        bulk_ops.append(UpdateOne(
                            filter={'_id': doc_id},
                            update={'$set': doc},
                            upsert=True
                        ))
                
                if bulk_ops:
                    result = self.collection.bulk_write(bulk_ops, ordered=False)
                    # Count both upserted (new) and modified (updated) documents
                    upserted_count = result.upserted_count + result.modified_count + result.inserted_count
                    total_upserted += upserted_count
                    logger.info(f"Batch {i//batch_size + 1}: {result.upserted_count} new, {result.modified_count} updated, {result.inserted_count} inserted")
                else:
                    logger.warning(f"Batch {i//batch_size + 1}: No valid documents with 'id' field found")
                
        except Exception as e:
            logger.error(f"Error upserting batch data: {e}")
        
        return total_upserted
    
    def read_by_ticker_range(self, ticker: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Read stock data for a ticker within a date range. If no dates provided, returns all data for ticker."""
        try:
            query = {"Ticker": ticker}
            
            # Add date range filter if provided
            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = pd.to_datetime(start_date)
                if end_date:
                    date_query["$lte"] = pd.to_datetime(end_date)
                query["Datetime"] = date_query
            
            cursor = self.collection.find(query).sort("Datetime", 1)
            results = list(cursor)
            
            logger.info(f"Found {len(results)} records for ticker {ticker}")
            return results
            
        except Exception as e:
            logger.error(f"Error reading data for ticker {ticker}: {e}")
            return []
    
    def read_latest_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Read the latest stock data for a ticker based on datetime."""
        try:
            query = {"Ticker": ticker}
            result = self.collection.find(query).sort("Datetime", -1).limit(1)
            
            latest = list(result)
            if latest:
                logger.info(f"Found latest record for ticker {ticker}")
                return latest[0]
            else:
                logger.info(f"No records found for ticker {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading latest data for ticker {ticker}: {e}")
            return None
    
    def update(self, record_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a stock price record by _id."""
        try:
            # Process datetime if it's in update data
            if 'Datetime' in update_data and isinstance(update_data['Datetime'], str):
                update_data['Datetime'] = pd.to_datetime(update_data['Datetime'])
                
            result = self.collection.update_one(
                {"_id": record_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated record with ID: {record_id}")
                return True
            else:
                logger.warning(f"No record found with ID: {record_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating record {record_id}: {e}")
            return False
    
    def delete(self, record_id: str) -> bool:
        """Delete a stock price record by _id."""
        try:
            result = self.collection.delete_one({"_id": record_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted record with ID: {record_id}")
                return True
            else:
                logger.warning(f"No record found with ID: {record_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting record {record_id}: {e}")
            return False
    
    def delete_by_ticker(self, ticker: str) -> int:
        """Delete all records for a specific ticker."""
        try:
            result = self.collection.delete_many({"Ticker": ticker})
            logger.info(f"Deleted {result.deleted_count} records for ticker {ticker}")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting records for ticker {ticker}: {e}")
            return 0
    
    def get_all_tickers(self) -> List[str]:
        """Get list of all unique tickers in the collection."""
        try:
            tickers = self.collection.distinct("Ticker")
            logger.info(f"Found {len(tickers)} unique tickers")
            return tickers
            
        except Exception as e:
            logger.error(f"Error getting tickers: {e}")
            return []


# Global singleton instance
_stock_manager = StockPriceManager()

# Module-level functions that use the singleton
def initialize_stock_manager(db_manager: MongoDBClient, collection_name: str = "stock_prices"):
    """Initialize the global stock manager."""
    _stock_manager.initialize(db_manager, collection_name)

def create_stock_data(stock_data: Dict[str, Any]) -> bool:
    """Create a single stock price record."""
    return _stock_manager.create(stock_data)

def create_many_stock_data(stock_data_list: List[Dict[str, Any]], batch_size: int = 1000) -> int:
    """Create multiple stock price records in batches."""
    return _stock_manager.create_many(stock_data_list, batch_size)

def get_stock_data_by_range(ticker: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get stock data for a ticker within a date range."""
    return _stock_manager.read_by_ticker_range(ticker, start_date, end_date)

def get_latest_stock_data(ticker: str) -> Optional[Dict[str, Any]]:
    """Get the latest stock data for a ticker."""
    return _stock_manager.read_latest_by_ticker(ticker)

def update_stock_data(record_id: str, update_data: Dict[str, Any]) -> bool:
    """Update a stock price record by _id."""
    return _stock_manager.update(record_id, update_data)

def delete_stock_data(record_id: str) -> bool:
    """Delete a stock price record by _id."""
    return _stock_manager.delete(record_id)

def delete_ticker_data(ticker: str) -> int:
    """Delete all records for a specific ticker."""
    return _stock_manager.delete_by_ticker(ticker)

def get_all_stock_tickers() -> List[str]:
    """Get list of all unique tickers."""
    return _stock_manager.get_all_tickers()