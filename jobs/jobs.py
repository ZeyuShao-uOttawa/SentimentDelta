from flask_apscheduler import APScheduler
from logger import get_logger
from datetime import datetime, timedelta
import pandas as pd
import sys
import os

from utils.scraper import get_article_text

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobs.yahoo_stock_price import process_ticker_data
from db.stock_price import (
    create_many_stock_data,
    get_latest_stock_data
)
from config.config import ApiConfig
from jobs.yahoo_stock_news import YahooFinanceScraper
from jobs.finviz_stock_news import scrape_finviz_ticker_news
from db.news import (
    create_many_news, 
    get_latest_news_by_ticker,
    get_news_by_url
)
from utils.sentiment import finbert_sentiment
from utils.embeddings import get_embeddings
from datetime import datetime

logger = get_logger(__name__)

def setup_scheduler(app):
    """Initialize and configure the scheduler with the Flask app"""
    scheduler = APScheduler()
    scheduler.init_app(app)
    
    # Register all scheduled jobs
    register_jobs(scheduler)
    
    scheduler.start()
    return scheduler

def fetch_and_store_stock_prices():
    """Fetch and store stock prices for all configured tickers."""
    
    if not ApiConfig.MONGODB_URI:
        logger.error("Configuration not initialized")
        return
    
    tickers = ApiConfig.TICKERS
    fallback_days = ApiConfig.STOCK_FALLBACK_DAYS
    interval = ApiConfig.DATA_INTERVAL
    
    logger.info(f"Starting stock price fetch for {len(tickers)} tickers: {tickers}")
    
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
            
            # Save data immediately after processing each ticker
            if ticker_data and len(ticker_data) > 0:
                try:
                    upserted_count = create_many_stock_data(ticker_data)
                    logger.info(f"Successfully saved {upserted_count} stock price records for {ticker}")
                except Exception as e:
                    logger.error(f"Error storing stock data for {ticker}: {str(e)}", exc_info=True)
            else:
                logger.info(f"No new data available for {ticker}")
                
        except Exception as e:
            logger.error(f"Error processing ticker {ticker}: {str(e)}", exc_info=True)
            continue

def fetch_and_store_stock_news():
    """Fetch and store stock news articles."""
    
    if not ApiConfig.MONGODB_URI:
        logger.error("Configuration not initialized")
        return
    
    tickers = ApiConfig.TICKERS
    news_fetch_days = ApiConfig.STOCK_NEWS_FETCH_DAYS
    
    logger.info(f"Starting stock news fetch for {len(tickers)} tickers: {tickers}")
    
    scraper = YahooFinanceScraper()
    
    for ticker in tickers:
        try:
            logger.info(f"Processing ticker: {ticker}")
            
            # Get latest news from database
            latest_news = get_latest_news_by_ticker(ticker)
            
            if latest_news:
                latest_date = latest_news.get('date')
                logger.info(f"Latest news for {ticker} found on {latest_date}. Fetching newer articles")
                
                # Calculate target days based on latest news date
                if latest_date:
                    try:
                        latest_date_obj = datetime.strptime(latest_date, '%Y-%m-%d')
                        days_since_latest = (datetime.now() - latest_date_obj).days
                        # Fetch a bit more than needed to ensure we don't miss anything
                        target_days = max(0, days_since_latest - 1)
                    except:
                        target_days = news_fetch_days
                else:
                    target_days = news_fetch_days
            else:
                # No news found, fetch last N days
                logger.info(f"No news found for {ticker}. Fetching last {news_fetch_days} days")
                target_days = news_fetch_days
            
            logger.info(f"Fetching news for ticker: {ticker} (target_days={target_days})")
            news_items = scraper.scrape(ticker, target_days=target_days, exact_day_only=False)
            
            if news_items and len(news_items) > 0:
                # Process each news item with sentiment and embeddings
                processed_items = []
                
                for article in news_items:
                    try:
                        # Skip if essential fields are missing
                        if not all(k in article for k in ("title", "url", "date", "body")):
                            continue
                        
                        # Generate sentiment analysis
                        sentiment = finbert_sentiment(article["title"] + " " + (article["body"] or ""))
                        
                        # Generate embeddings
                        embedding_text = f"{ticker} {article['title']} {article['body'] or ''} {article['date']}"
                        embedding = get_embeddings(embedding_text)
                        if embedding is not None:
                            embedding = embedding.tolist()
                        
                        # Create document in the required format
                        doc = {
                            "ticker": ticker,
                            "source": "yahoo_finance",
                            "title": article["title"],
                            "url": article["url"],
                            "date": article["date"],
                            "body": article.get("body"),
                            "embedding": embedding,
                            "ingested_at": datetime.now(),
                            "sentiment": {
                                "score": sentiment["score"],
                                "positive": sentiment["positive"],
                                "neutral": sentiment["neutral"],
                                "negative": sentiment["negative"]
                            }
                        }
                        
                        processed_items.append(doc)
                        
                    except Exception as e:
                        logger.warning(f"Error processing article for {ticker}: {e}")
                        continue
                
                # Save processed news immediately after processing each ticker
                if processed_items:
                    try:
                        upserted_count = create_many_news(processed_items)
                        logger.info(f"Successfully saved {upserted_count} news articles for {ticker}")
                    except Exception as e:
                        logger.error(f"Error storing news for {ticker}: {str(e)}", exc_info=True)
                else:
                    logger.info(f"No valid news articles processed for {ticker}")
            else:
                logger.info(f"No new news articles found for {ticker}")
                
        except Exception as e:
            logger.error(f"Error fetching news for ticker {ticker}: {str(e)}", exc_info=True)
            continue

def fetch_and_store_finviz_news():
    """Fetch and store stock news articles from Finviz."""
    
    if not ApiConfig.MONGODB_URI:
        logger.error("Configuration not initialized")
        return
    
    tickers = ApiConfig.TICKERS
    
    logger.info(f"Starting Finviz news fetch for {len(tickers)} tickers: {tickers}")
    
    for ticker in tickers:
        try:
            logger.info(f"Processing ticker: {ticker}")
            
            # Get latest news from database for this ticker
            latest_news = get_latest_news_by_ticker(ticker)
            
            if latest_news:
                latest_date = latest_news.get('date')
                logger.info(f"Latest Finviz news for {ticker} found on {latest_date}. Fetching newer articles")
            else:
                logger.info(f"No Finviz news found for {ticker}. Fetching available articles")
            
            logger.info(f"Fetching Finviz news for ticker: {ticker}")
            news_items = scrape_finviz_ticker_news(ticker, custom_logger=logger)
            
            if news_items and len(news_items) > 0:
                # Process each news item with sentiment and embeddings
                processed_items = []
                
                for article in news_items:
                    try:
                        # Skip if essential fields are missing
                        if not all(k in article for k in ("title", "url", "date")):
                            continue
                        
                        # Skip if URL already exists in database
                        if get_news_by_url(article["url"]):
                            logger.debug(f"URL already exists in database: {article['url']}")
                            continue

                        # Get the body here
                        body = get_article_text(article["url"]) or None
                        
                        # Generate sentiment analysis
                        sentiment = finbert_sentiment(article["title"] + " " + (body or ""))
                        
                        # Generate embeddings
                        embedding_text = f"{ticker} {article['title']} {body or ''}"
                        embedding = get_embeddings(embedding_text)
                        if embedding is not None:
                            embedding = embedding.tolist()
                        
                        # Create document in the required format
                        doc = {
                            "ticker": ticker,
                            "source": "finviz",
                            "title": article["title"],
                            "url": article["url"],
                            "date": article["date"],
                            "body": body,
                            "embedding": embedding,
                            "ingested_at": datetime.now(),
                            "timestamp": article["timestamp"],
                            "sentiment": {
                                "score": sentiment["score"],
                                "positive": sentiment["positive"],
                                "neutral": sentiment["neutral"],
                                "negative": sentiment["negative"]
                            }
                        }
                        
                        processed_items.append(doc)
                        
                    except Exception as e:
                        logger.warning(f"Error processing Finviz article for {ticker}: {e}")
                        continue
                
                # Save processed news immediately after processing each ticker
                if processed_items:
                    try:
                        upserted_count = create_many_news(processed_items)
                        logger.info(f"Successfully saved {upserted_count} Finviz news articles for {ticker}")
                    except Exception as e:
                        logger.error(f"Error storing Finviz news for {ticker}: {str(e)}", exc_info=True)
                else:
                    logger.info(f"No valid Finviz news articles processed for {ticker}")
            else:
                logger.info(f"No new Finviz news articles found for {ticker}")
                
        except Exception as e:
            logger.error(f"Error fetching Finviz news for ticker {ticker}: {str(e)}", exc_info=True)
            continue

def register_jobs(scheduler):
    """Register all scheduled jobs"""
    
    fetch_interval_hours = ApiConfig.STOCK_FETCH_INTERVAL_HOURS

    # Health check job - reduced frequency
    @scheduler.task('interval', id='health_check', minutes=30)
    def health_check_job():
        logger.info("Scheduler health check - system running normally")
    
    # Stock price fetching job - runs every N hours (configurable)
    @scheduler.task('interval', id='stock_price_fetcher', hours=fetch_interval_hours)
    def stock_price_job():
        logger.info(f"Running scheduled stock price fetch job (every {fetch_interval_hours} hours)")
        fetch_and_store_stock_prices()

    # Stock news fetching job - runs every N hours (configurable)
    @scheduler.task('interval', id='stock_news_fetcher', hours=fetch_interval_hours)
    def stock_news_job():
        logger.info(f"Running scheduled stock news fetch job (every {fetch_interval_hours} hours)")
        fetch_and_store_stock_news()
    
    # Finviz news fetching job - runs every N hours (configurable)
    @scheduler.task('interval', id='finviz_news_fetcher', hours=fetch_interval_hours)
    def finviz_news_job():
        logger.info(f"Running scheduled Finviz news fetch job (every {fetch_interval_hours} hours)")
        fetch_and_store_finviz_news()
    
    # Schedule initial fetch to run after server startup delay
    @scheduler.task('date', id='initial_stock_fetch', run_date=datetime.now() + timedelta(seconds=30))
    def initial_stock_fetch():
        logger.info("Running delayed initial stock price fetch after server startup")
        fetch_and_store_stock_prices()
    
    @scheduler.task('date', id='initial_stock_news_fetch', run_date=datetime.now() + timedelta(seconds=60))
    def initial_stock_news_fetch():
        logger.info("Running delayed initial stock news fetch after server startup")
        fetch_and_store_stock_news()
    
    @scheduler.task('date', id='initial_finviz_news_fetch', run_date=datetime.now() + timedelta(seconds=90))
    def initial_finviz_news_fetch():
        logger.info("Running delayed initial Finviz news fetch after server startup")
        fetch_and_store_finviz_news()