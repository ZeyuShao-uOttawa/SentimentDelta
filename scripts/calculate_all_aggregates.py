from datetime import datetime, timedelta
from pymongo.errors import DuplicateKeyError

from utils.daily_aggregate import daily_aggregate
from config.config import ApiConfig
from db.client import MongoDBClient
from db.news_queries import get_news_by_ticker_and_date, initialize_news_manager
from db.aggregates_queries import create_aggregate, initialize_aggregates_manager
from db.news_queries import get_news_by_ticker_and_date
from db.aggregates_queries import create_aggregate, update_aggregate_by_ticker_and_date

from logger import get_logger

logger = get_logger(__name__)

def calculate_aggregate(search_date, ticker):
    """
    Function to update all documents in the news collection with a sentiment score
    """
    projection = {
        "_id": 0,
        "sentiment": 1
    }

    date_str = search_date.strftime("%Y-%m-%d")

    docs = get_news_by_ticker_and_date(ticker, date_str, projection)

    if docs:
        features = daily_aggregate(docs)
        features["date"] = date_str
        features["ticker"] = ticker

        logger.info(f"Calculated features: {features}, for date: {date_str}, ticker: {ticker}")

        # determine if search_date is today
        date_obj = search_date.date() if isinstance(search_date, datetime) else search_date
        if date_obj == datetime.today().date():
            update_aggregate_by_ticker_and_date(ticker, date_str, features)
        else:
            create_aggregate(features)
    else:
        logger.info(f"No documents found for {ticker} on {date_str}")

if __name__ == "__main__":
    TICKERS = ["AAPL", "AMZN", "GOOGL", "META", "MSFT", "NFLX", "NVDA", "TSLA"]
    start_str = "2026-01-01"
    end_str = "2026-01-22"

    start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_str, "%Y-%m-%d").date()

    db = MongoDBClient(ApiConfig.MONGODB_URI, ApiConfig.MONGO_DB)

    if not db.connect():
        logger.error("Failed to connect to MongoDB")

    initialize_news_manager(db)
    initialize_aggregates_manager(db)

    current_date = start_date
    while current_date <= end_date:
        for ticker in TICKERS:
            print(current_date.strftime("%Y-%m-%d"))
            calculate_aggregate(current_date, ticker)

        current_date += timedelta(days=1)