"""Simple configuration for SentimentDelta."""

import os
from dotenv import load_dotenv

load_dotenv()

def get_config():
    """Get configuration from environment variables."""
    return {
        'mongodb_uri': os.getenv('MONGODB_URI'),
        'database_name': os.getenv('DATABASE_NAME', 'stock_market_db'),
        'tickers': [t.strip().upper() for t in os.getenv('TICKERS', 'AAPL,GOOGL,MSFT,TSLA,AMZN').split(',')],
        'batch_size': int(os.getenv('BATCH_SIZE', '1000')),
        'data_period': os.getenv('DATA_PERIOD', '1mo'),
        'data_interval': os.getenv('DATA_INTERVAL', '15m'),
        'stock_fetch_interval_hours': int(os.getenv('STOCK_FETCH_INTERVAL_HOURS', '3')),
        'stock_fallback_days': int(os.getenv('STOCK_FALLBACK_DAYS', '3')),
        'scraping_max_pages': int(os.getenv('SCRAPING_MAX_PAGES', '10')),
        'embedding_model': os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'log_file': os.getenv('LOG_FILE')
    }

class ApiConfig:
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB = os.getenv("MONGO_DB")
    LOG_LEVEL = "INFO"
    LOG_FILE = "server.log"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    TICKERS = [t.strip().upper() for t in os.getenv('TICKERS', 'AAPL').split(',')]