"""Simple configuration for SentimentDelta."""

import os
from dotenv import load_dotenv

load_dotenv()

class ApiConfig:
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB = os.getenv("MONGO_DB")
    MONGODB_URI = os.getenv('MONGODB_URI')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'stock_market_db')
    TICKERS = [t.strip().upper() for t in os.getenv('TICKERS', 'AAPL,GOOGL,MSFT,TSLA,AMZN').split(',')]
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '1000'))
    DATA_INTERVAL = os.getenv('DATA_INTERVAL', '15m')
    STOCK_FETCH_INTERVAL_HOURS = int(os.getenv('STOCK_FETCH_INTERVAL_HOURS', '3'))
    STOCK_FALLBACK_DAYS = int(os.getenv('STOCK_FALLBACK_DAYS', '3'))
    SCRAPING_MAX_PAGES = int(os.getenv('SCRAPING_MAX_PAGES', '10'))
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')