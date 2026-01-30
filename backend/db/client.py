from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
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
        self.db.news.create_index([("url", ASCENDING), ("ticker", ASCENDING)], unique=True)

        self.db.news.create_index([("ticker", ASCENDING), ("date", ASCENDING)])
        
        self.db.aggregates.create_index([("ticker", ASCENDING), ("date", ASCENDING)], unique=True)

        self.db.stock_prices.create_index([("Ticker", ASCENDING), ("Datetime", ASCENDING)], unique=True)
    
    def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.logger.info("MongoDB connection closed")