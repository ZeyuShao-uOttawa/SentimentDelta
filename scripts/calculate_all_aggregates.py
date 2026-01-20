from datetime import datetime, timedelta
from utils.sentiment import finbert_sentiment
from utils.daily_aggregate import daily_aggregate
import os
from dotenv import load_dotenv

from db.client import MongoDBClient
from db.news_queries import get_news_by_ticker_and_date
from db.aggregates_queries import create_aggregate

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

        create_aggregate(features)
    else:
        logger.info(f"No documents found for {ticker} on {date_str}")