from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
from sentence_transformers import SentenceTransformer
from logger import get_logger

class MongoDBClient:
    def __init__(self, uri: str, database_name: str):
        self.uri = uri
        self.database_name = database_name
        self.logger = get_logger(__name__)
        self.client: MongoClient | None = None
        self.db = None
    
    def connect(self) -> None:
        """Create MongoDB client and verify connection."""
        try:
            self.logger.info("Connecting to MongoDB")
            self.client = MongoClient(self.uri)
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]

            self.logger.info("Connected to MongoDB")

            self._create_indexes()
            return True
        except Exception as e:
            self.logger.exception("Error connecting to MongoDB")
            return False

    def _create_indexes(self) -> None:
        self.db.news.create_index("url", unique=True)

        self.db.news.create_index([("ticker", ASCENDING), ("date", ASCENDING)])
        
        self.db.stock_prices.create_index([("Ticker", ASCENDING), ("Datetime", ASCENDING)], unique=True,)

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
    
    def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.logger.info("MongoDB connection closed")