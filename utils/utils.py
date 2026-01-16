"""Utility functions for data processing and database operations."""

import datetime
from typing import Optional

from tqdm import tqdm
from config.config import ApiConfig
from db.database import MongoDBManager


def iso_to_milliseconds(iso_timestamp: str) -> int:
    """
    Convert ISO timestamp to milliseconds.
    
    Args:
        iso_timestamp: ISO format timestamp (e.g., "2026-01-08T10:23:00")
        
    Returns:
        Timestamp in milliseconds
    """
    try:
        # Parse ISO format timestamp
        dt = datetime.datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        # Convert to milliseconds
        return int(dt.timestamp() * 1000)
    except (ValueError, TypeError) as e:
        print(f"Error converting ISO timestamp {iso_timestamp}: {e}")
        return None


def normalize_timestamp(timestamp) -> int:
    """
    Normalize timestamp to milliseconds format.
    
    Args:
        timestamp: Either int (milliseconds), string (milliseconds or ISO format)
        
    Returns:
        Timestamp in milliseconds
    """
    if isinstance(timestamp, int):
        return timestamp
    elif isinstance(timestamp, str):
        # First try to parse as integer (string representation of milliseconds)
        try:
            timestamp_int = int(timestamp)
            # Check if it's a reasonable timestamp (between 1970 and 2100)
            if 0 < timestamp_int < 4000000000000:  # roughly year 2100 in milliseconds
                return timestamp_int
        except ValueError:
            pass
        
        # If not a valid integer, try ISO format
        return iso_to_milliseconds(timestamp)
    else:
        print(f"Unknown timestamp format: {type(timestamp)} - {timestamp}")
        return None


def timestamp_to_date(timestamp: int) -> str:
    """
    Convert timestamp to yyyy-mm-dd format.
    
    Args:
        timestamp: Timestamp in milliseconds (e.g., 1768242489743)
        
    Returns:
        Date string in yyyy-mm-dd format
    """
    try:
        # Convert milliseconds to seconds
        timestamp_seconds = timestamp / 1000
        # Convert to datetime
        dt = datetime.datetime.fromtimestamp(timestamp_seconds)
        # Format as yyyy-mm-dd
        return dt.strftime('%Y-%m-%d')
    except (ValueError, TypeError, OSError) as e:
        print(f"Error converting timestamp {timestamp}: {e}")
        return None


def add_date_field_to_collections(db_manager: MongoDBManager) -> dict:
    """
    Add date field to all documents in finvis_news and marketwatch_news collections
    based on their timestamp field.
    
    Args:
        db_manager: Connected MongoDBManager instance
        
    Returns:
        Dictionary with update results for each collection
    """
    collections = ['marketwatch_news']
    results = {}
    
    if db_manager.db is None:
        print("ERROR: Database not connected")
        return {"error": "Database not connected"}
    
    print(f"Processing {len(collections)} collections: {collections}")
    
    for collection_name in collections:
        print(f"\nProcessing collection: {collection_name}")
        try:
            collection = db_manager.db[collection_name]
            
            # Get count of documents with timestamp field
            total_docs = collection.count_documents({"timestamp": {"$exists": True}})
            print(f"Found {total_docs} documents with timestamp field in {collection_name}")
            
            if total_docs == 0:
                print(f"No documents with timestamp found in {collection_name}")
                results[collection_name] = {
                    "updated": 0,
                    "failed": 0,
                    "total_processed": 0
                }
                continue
            
            # Get all documents with timestamp field
            docs_with_timestamp = collection.find({"timestamp": {"$exists": True}})
            
            updated_count = 0
            failed_count = 0
            
            print(f"Processing documents in {collection_name}...")
            for doc in tqdm(docs_with_timestamp, total=total_docs, desc=f"Processing {collection_name}"):
                original_timestamp = doc.get('timestamp')
                if original_timestamp:
                    # Normalize timestamp to milliseconds
                    timestamp_ms = normalize_timestamp(original_timestamp)
                    
                    if timestamp_ms:
                        # Convert timestamp to date
                        date_str = timestamp_to_date(timestamp_ms)
                        
                        if date_str:
                            # Update document with normalized timestamp and date field
                            collection.update_one(
                                {"_id": doc["_id"]},
                                {"$set": {
                                    "timestamp": timestamp_ms,  # Normalize timestamp to milliseconds
                                    "date": date_str
                                }}
                            )
                            updated_count += 1
                        else:
                            failed_count += 1
                            print(f"Failed to convert timestamp to date for document {doc['_id']}: {original_timestamp}")
                    else:
                        failed_count += 1
                        print(f"Failed to normalize timestamp for document {doc['_id']}: {original_timestamp}")
                else:
                    failed_count += 1
                    print(f"Document {doc['_id']} has no timestamp value")
            
            results[collection_name] = {
                "updated": updated_count,
                "failed": failed_count,
                "total_processed": updated_count + failed_count
            }
            
            print(f"Completed {collection_name}: {updated_count} updated, {failed_count} failed")
            
        except Exception as e:
            print(f"ERROR processing collection {collection_name}: {str(e)}")
            results[collection_name] = {"error": str(e)}
    
    return results


def add_date_field_simple(mongodb_uri: str = "mongodb://localhost:27017/", 
                         database_name: str = "meet_data") -> dict:
    """
    Simple function to add date field to collections.
    Creates connection, adds date fields, and closes connection.
    
    Args:
        mongodb_uri: MongoDB connection URI
        database_name: Database name
        
    Returns:
        Dictionary with update results
    """
    print(f"Connecting to MongoDB at: {mongodb_uri}")
    print(f"Database: {database_name}")
    
    db_manager = MongoDBManager(mongodb_uri, database_name)
    
    try:
        print("Attempting to connect to database...")
        if not db_manager.connect():
            print("ERROR: Failed to connect to database")
            return {"error": "Failed to connect to database"}
        
        print("Database connection successful!")
        results = add_date_field_to_collections(db_manager)
        return results
        
    except Exception as e:
        print(f"ERROR in add_date_field_simple: {str(e)}")
        return {"error": str(e)}
    finally:
        print("Disconnecting from database...")
        db_manager.disconnect()
        print("Database connection closed.")


if __name__ == "__main__":
    # Example usage
    print("Starting date field update process...")
    
    try:
        print(f"Configuration loaded successfully")
        print(f"MongoDB URI: {ApiConfig.MONGODB_URI}")
        print(f"Database name: {ApiConfig.DATABASE_NAME}")
        
        results = add_date_field_simple(ApiConfig.MONGODB_URI, ApiConfig.DATABASE_NAME)
        
        print("\n" + "="*50)
        print("Date field update results:")
        print("="*50)
        
        for collection, result in results.items():
            if "error" in result:
                print(f"❌ {collection}: Error - {result['error']}")
            else:
                print(f"✅ {collection}:")
                print(f"   - Updated: {result['updated']} docs")
                print(f"   - Failed: {result['failed']} docs")
                print(f"   - Total processed: {result['total_processed']} docs")
        
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
