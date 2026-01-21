from logger import get_logger
from datetime import datetime, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from utils.scraper import get_article_text
from db.stock_price_queries import (
    create_many_stock_data,
    get_latest_stock_data
)
from config.config import ApiConfig
from scrapers.yahoo_stock_news import scrape_yahoo_finance
from scrapers.finviz_stock_news import scrape_finviz_ticker_news
from scrapers.yahoo_stock_price import process_ticker_data
from db.news_queries import (
    create_many_news, 
    get_latest_news_by_ticker,
    get_news_by_url,
    get_news_dates
)
from db.aggregates_queries import get_aggregate_dates
from scripts.calculate_all_aggregates import calculate_aggregate
from utils.sentiment import finbert_sentiment
from utils.embeddings import get_embeddings

logger = get_logger(__name__)

MAX_WORKERS = 10

def get_article_body_safe(url):
    """Safely fetch article body."""
    try:
        return get_article_text(url) if url else None
    except Exception as e:
        logger.warning(f"Error fetching {url}: {e}")
        return None

def process_article(ticker, article, body):
    """Process a single article with sentiment and embeddings."""
    try:
        if not all(k in article for k in ("title", "url", "date")):
            return None
        
        if get_news_by_url(article["url"]):
            return None
        
        sentiment = finbert_sentiment(article["title"] + " " + (body or ""))
        
        embedding_text = f"{ticker} {article['title']} {body or ''} {article.get('date', '')}"
        embedding = get_embeddings(embedding_text)
        if embedding is not None:
            embedding = embedding.tolist()
        
        doc = {
            "ticker": ticker,
            "source": article.get("source", "yahoo_finance"),
            "title": article["title"],
            "url": article["url"],
            "date": article["date"],
            "body": body,
            "embedding": embedding,
            "ingested_at": datetime.now(),
            "sentiment": {
                "score": sentiment["score"],
                "positive": sentiment["positive"],
                "neutral": sentiment["neutral"],
                "negative": sentiment["negative"]
            }
        }
        
        if "timestamp" in article:
            doc["timestamp"] = article["timestamp"]
        
        return doc
    except Exception as e:
        logger.warning(f"Error processing article: {e}")
        return None

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
            latest_data = get_latest_stock_data(ticker)
            
            if latest_data:
                latest_datetime = latest_data['Datetime']
                if isinstance(latest_datetime, str):
                    latest_datetime = pd.to_datetime(latest_datetime)
                
                start_time = latest_datetime + timedelta(minutes=15)
                start_date = start_time.strftime('%Y-%m-%d')
                
                logger.info(f"Latest data for {ticker} found at {latest_datetime}. Fetching from {start_date}")
                
                if start_time < datetime.now():
                    ticker_data = process_ticker_data(ticker=ticker, interval=interval, start=start_date, end=None)
                else:
                    logger.info(f"Latest data for {ticker} is up to date")
                    ticker_data = None
            else:
                end_date = datetime.now()
                start_date = (end_date - timedelta(days=fallback_days)).strftime('%Y-%m-%d')
                logger.info(f"No data found for {ticker}. Fetching last {fallback_days} days from {start_date}")
                ticker_data = process_ticker_data(ticker=ticker, interval=interval, start=start_date, end=None)
            
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

def fetch_and_store_yahoo_news():
    """Fetch and store stock news articles."""
    if not ApiConfig.MONGODB_URI:
        logger.error("Configuration not initialized")
        return
    
    tickers = ApiConfig.TICKERS
    news_fetch_days = ApiConfig.STOCK_NEWS_FETCH_DAYS
    
    logger.info(f"Starting stock news fetch for {len(tickers)} tickers: {tickers}")
    
    for ticker in tickers:
        try:
            logger.info(f"Processing ticker: {ticker}")
            latest_news = get_latest_news_by_ticker(ticker)
            
            if latest_news:
                latest_date = latest_news.get('date')
                logger.info(f"Latest news for {ticker} found on {latest_date}. Fetching newer articles")
                
                if latest_date:
                    try:
                        latest_date_obj = datetime.strptime(latest_date, '%Y-%m-%d')
                        days_since_latest = (datetime.now() - latest_date_obj).days
                        target_days = max(0, days_since_latest - 1)
                    except:
                        target_days = news_fetch_days
                else:
                    target_days = news_fetch_days
            else:
                logger.info(f"No news found for {ticker}. Fetching last {news_fetch_days} days")
                target_days = news_fetch_days
            
            logger.info(f"Fetching news for ticker: {ticker} (target_days={target_days})")
            news_items = scrape_yahoo_finance(ticker, target_days=target_days, exact_day_only=False)
            
            if news_items and len(news_items) > 0:
                # Fetch all bodies in parallel
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    bodies = list(executor.map(lambda a: get_article_body_safe(a.get("url")), news_items))
                
                # Process articles
                processed_items = []
                for article, body in zip(news_items, bodies):
                    doc = process_article(ticker, article, body)
                    if doc:
                        processed_items.append(doc)
                
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
            latest_news = get_latest_news_by_ticker(ticker)
            
            if latest_news:
                latest_date = latest_news.get('date')
                logger.info(f"Latest Finviz news for {ticker} found on {latest_date}. Fetching newer articles")
            else:
                logger.info(f"No Finviz news found for {ticker}. Fetching available articles")
            
            logger.info(f"Fetching Finviz news for ticker: {ticker}")
            news_items = scrape_finviz_ticker_news(ticker, custom_logger=logger)
            
            if news_items and len(news_items) > 0:
                # Add source tag
                for article in news_items:
                    article["source"] = "finviz"
                
                # Fetch all bodies in parallel
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    bodies = list(executor.map(lambda a: get_article_body_safe(a.get("url")), news_items))
                
                # Process articles
                processed_items = []
                for article, body in zip(news_items, bodies):
                    doc = process_article(ticker, article, body)
                    if doc:
                        processed_items.append(doc)
                
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

def process_missing_aggregates():
    """Process missing aggregates by comparing news dates vs aggregate dates for each ticker."""
    if not ApiConfig.MONGODB_URI:
        logger.error("Configuration not initialized")
        return
    
    tickers = ApiConfig.TICKERS
    logger.info(f"Starting missing aggregates processing for {len(tickers)} tickers: {tickers}")
    
    total_processed = 0
    total_missing = 0
    
    for ticker in tickers:
        try:
            logger.info(f"Processing missing aggregates for ticker: {ticker}")
            
            news_dates = get_news_dates(ticker)
            logger.info(f"Found {len(news_dates)} news dates for {ticker}: {news_dates[:5]}{'...' if len(news_dates) > 5 else ''}")
            
            aggregate_dates = get_aggregate_dates(ticker)
            logger.info(f"Found {len(aggregate_dates)} aggregate dates for {ticker}: {aggregate_dates[:5]}{'...' if len(aggregate_dates) > 5 else ''}")
            
            missing_dates = sorted(list(set(news_dates) - set(aggregate_dates)))
            
            if missing_dates:
                logger.info(f"Found {len(missing_dates)} missing aggregate dates for {ticker}: {missing_dates}")
                total_missing += len(missing_dates)
                
                for date_str in missing_dates:
                    try:
                        logger.info(f"Processing aggregate for {ticker} on {date_str}")
                        search_date = datetime.strptime(date_str, "%Y-%m-%d")
                        calculate_aggregate(search_date, ticker)
                        total_processed += 1
                        logger.info(f"Successfully processed aggregate for {ticker} on {date_str}")
                    except Exception as e:
                        logger.error(f"Error processing aggregate for {ticker} on {date_str}: {str(e)}", exc_info=True)
                        continue
            else:
                logger.info(f"No missing aggregates found for {ticker} - all news dates have corresponding aggregates")
                
        except Exception as e:
            logger.error(f"Error processing missing aggregates for ticker {ticker}: {str(e)}", exc_info=True)
            continue
    
    logger.info(f"Missing aggregates processing complete. Processed {total_processed}/{total_missing} missing aggregates across {len(tickers)} tickers")