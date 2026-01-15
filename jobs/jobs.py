from flask_apscheduler import APScheduler
from logger import get_logger
from datetime import datetime, timedelta
import pandas as pd
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobs.yahoo_stock_price import process_ticker_data
from db.stock_price import (
    create_many_stock_data,
    get_latest_stock_data
)
from config.config import get_config

logger = get_logger(__name__)
config = get_config()

def setup_scheduler(app):
    """Initialize and configure the scheduler with the Flask app"""
    scheduler = APScheduler()
    scheduler.init_app(app)
    
    # Register all scheduled jobs
    register_jobs(scheduler)
    
    # Run stock price fetching job immediately on startup
    # logger.info("Running initial stock price fetch on startup")
    # fetch_and_store_stock_prices()
    
    scheduler.start()
    return scheduler

def fetch_and_store_stock_prices():
    """Fetch and store stock prices for all configured tickers."""
    
    if not config:
        logger.error("Configuration not initialized")
        return
    
    tickers = config['tickers']
    fallback_days = config['stock_fallback_days']
    interval = config['data_interval']
    
    logger.info(f"Starting stock price fetch for {len(tickers)} tickers: {tickers}")
    
    all_data = []
    
    for ticker in tickers:
        try:
            logger.info(f"Processing ticker: {ticker}")
            
            # Get latest data from database
            latest_data = get_latest_stock_data(ticker)
            
            if latest_data:
                # Get timestamp from latest data and fetch from that point
                latest_datetime = latest_data['Datetime']
                if isinstance(latest_datetime, str):
                    latest_datetime = pd.to_datetime(latest_datetime)
                
                # Start from the next interval after the latest data
                start_time = latest_datetime + timedelta(minutes=15)
                start_date = start_time.strftime('%Y-%m-%d')
                
                logger.info(f"Latest data for {ticker} found at {latest_datetime}. Fetching from {start_date}")
                
                # Only fetch if start_date is not in the future
                if start_time < datetime.now():
                    ticker_data = process_ticker_data(
                        ticker=ticker,
                        interval=interval,
                        start=start_date,
                        end=None
                    )
                else:
                    logger.info(f"Latest data for {ticker} is up to date")
                    ticker_data = None
            else:
                # No data found, fetch last N days
                end_date = datetime.now()
                start_date = (end_date - timedelta(days=fallback_days)).strftime('%Y-%m-%d')
                
                logger.info(f"No data found for {ticker}. Fetching last {fallback_days} days from {start_date}")
                
                ticker_data = process_ticker_data(
                    ticker=ticker,
                    interval=interval,
                    start=start_date,
                    end=None
                )
            
            if ticker_data and len(ticker_data) > 0:
                all_data.extend(ticker_data)
                logger.info(f"Fetched {len(ticker_data)} records for {ticker}")
            else:
                logger.info(f"No new data available for {ticker}")
                
        except Exception as e:
            logger.error(f"Error processing ticker {ticker}: {str(e)}", exc_info=True)
            continue
    
    # Store all data in database
    if all_data:
        try:
            upserted_count = create_many_stock_data(all_data)
            logger.info(f"Successfully upserted {upserted_count} stock price records")
        except Exception as e:
            logger.error(f"Error storing stock data: {str(e)}", exc_info=True)
    else:
        logger.info("No new stock data to store")


def register_jobs(scheduler):
    """Register all scheduled jobs"""
    
    fetch_interval_hours = config.get('stock_fetch_interval_hours', 3)
    
    # Stock price fetching job - runs every N hours (configurable)
    @scheduler.task('interval', id='stock_price_fetcher', hours=fetch_interval_hours)
    def stock_price_job():
        logger.info(f"Running scheduled stock price fetch job (every {fetch_interval_hours} hours)")
        fetch_and_store_stock_prices()
    
    # Health check job - reduced frequency
    @scheduler.task('interval', id='health_check', minutes=30)
    def health_check_job():
        logger.info("Scheduler health check - system running normally")
    
    # Schedule initial fetch to run after server startup delay
    @scheduler.task('date', id='initial_stock_fetch', run_date=datetime.now() + timedelta(seconds=30))
    def initial_stock_fetch():
        logger.info("Running delayed initial stock price fetch after server startup")
        fetch_and_store_stock_prices()