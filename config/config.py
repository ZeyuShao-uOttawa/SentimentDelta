"""Simple configuration for SentimentDelta."""

import os


def load_env():
    """Load environment variables from .env file."""
    try:
        with open('.env') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value
    except:
        pass


load_env()


def get_config():
    """Get configuration from environment variables."""
    return {
        'mongodb_uri': os.getenv('MONGODB_URI'),
        'database_name': os.getenv('DATABASE_NAME', 'stock_market_db'),
        'tickers': [t.strip().upper() for t in os.getenv('TICKERS', 'AAPL,GOOGL,MSFT,TSLA,AMZN,NVDA,META,NFLX').split(',')],
        'batch_size': int(os.getenv('BATCH_SIZE', '1000')),
        'data_period': os.getenv('DATA_PERIOD', '1mo'),
        'data_interval': os.getenv('DATA_INTERVAL', '1d'),
        'scraping_max_pages': int(os.getenv('SCRAPING_MAX_PAGES', '10')),
        'embedding_model': os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'log_file': os.getenv('LOG_FILE')
    }