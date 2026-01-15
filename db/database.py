"""Simple MongoDB operations."""

from typing import List, Dict, Any
from pymongo import MongoClient, errors
from sentence_transformers import SentenceTransformer
from logger import get_logger

logger = get_logger(__name__)

class MongoDBManager:
    """Simple MongoDB manager."""
    
    def __init__(self, mongodb_uri, database_name):
        logger.info("Initializing MongoDBManager")
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name
        self.client = None
        self.db = None
        self.embedding_model = None
    
    def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            return True
        except Exception as e:
            logger.error("Error connecting to MongoDB", e , exc_info=True)
            return False
    
    def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
    
    def insert_data(self, collection_name, data, batch_size=1000):
        """Insert data in batches."""
        collection = self.db[collection_name]
        # collection.delete_many({})  # Clear existing data
        
        if not data:
            return 0

        # Insert in batches
        total_inserted = 0
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            collection.insert_many(batch)
            total_inserted += len(batch)
        
        return total_inserted
    
    def insert_single_doc(self, collection_name, doc):
        """Insert a single document."""
        collection = self.db[collection_name]

        if not doc:
            return False

        try:
            collection.insert_one(doc)
            return True
        except errors.DuplicateKeyError:
            return False

    def setup_embeddings(self, model_name):
        """Setup sentence transformer model."""
        try:
            self.embedding_model = SentenceTransformer(model_name)
            return True
        except Exception:
            return False
    
    def get_embeddings(self, texts):
        """Get embeddings for texts."""
        if not self.embedding_model:
            return None
        return self.embedding_model.encode(texts)