"""Simple SentimentDelta main script."""

from tqdm import tqdm
from config import get_config
from utils.logger import get_logger
from db.database import MongoDBManager
from data.data_processor import process_multiple_tickers
from data.scraper import scrape_multiple_marketwatch_tickers, scrape_marketwatch_ticker_news, scrape_finviz_ticker_news, scrape_multiple_finviz_tickers
from data.scrape_yahoo_finance import scrape_multiple_yahoo_tickers


def store_stock_data(db_manager, ticker_data, config, logger):
    """Store stock market data in the database.
    
    Args:
        db_manager: MongoDB manager instance
        ticker_data: Dictionary of ticker data from data processor
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        Dict with success/failure counts and details
    """
    results = {
        'successful': [],
        'failed': [],
        'total_records': 0
    }
    
    logger.info(f"Starting to store data for {len(ticker_data)} tickers")
    
    for ticker, data in tqdm(ticker_data.items(), desc="Storing stock data"):
        if data is None or data.empty:
            logger.warning(f"No data available for {ticker}")
            results['failed'].append(ticker)
            continue
        
        try:
            # Ensure all column names are strings
            data.columns = [str(col) for col in data.columns]
            
            # Convert to records for MongoDB
            records = data.to_dict('records')
            
            # Ensure all keys in records are strings
            clean_records = []
            for record in records:
                clean_record = {str(k): v for k, v in record.items()}
                clean_records.append(clean_record)
            
            total_inserted = db_manager.insert_data(
                f"{ticker}_data", 
                clean_records, 
                config['batch_size']
            )
            
            results['successful'].append(ticker)
            results['total_records'] += total_inserted
            logger.info(f"Successfully stored {total_inserted} records for {ticker}")
            
        except Exception as e:
            logger.error(f"Failed to store data for {ticker}: {e}")
            results['failed'].append(ticker)
    
    logger.info(f"Stock data storage complete: {len(results['successful'])} successful, {len(results['failed'])} failed")
    return results


def fetch_news_data(tickers, max_pages, logger):
    """Fetch relevant news data from news sources.
    
    Args:
        tickers: List of stock tickers to fetch news for
        max_pages: Maximum number of pages to scrape per ticker
        logger: Logger instance
        
    Returns:
        Dictionary of news articles by ticker
    """
    logger.info(f"Starting news fetch for {len(tickers)} tickers, max {max_pages} pages each")
    
    try:
        news_data = scrape_multiple_marketwatch_tickers(tickers, max_pages, logger)
        
        # Log summary
        total_articles = sum(len(articles) for articles in news_data.values())
        logger.info(f"News fetching complete: {total_articles} total articles collected")
        
        # Log per-ticker summary
        for ticker, articles in news_data.items():
            logger.info(f"{ticker}: {len(articles)} articles")
            
        return news_data
        
    except Exception as e:
        logger.error(f"Failed to fetch news data: {e}")
        return {}


def store_news_data(db_manager, news_data, config, logger, news_source="news"):
    """Store news data with embeddings in the database.
    
    Args:
        db_manager: MongoDB manager instance
        news_data: Dictionary of news articles by ticker
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        Dict with success/failure counts and details
    """
    results = {
        'successful': [],
        'failed': [],
        'total_articles': 0
    }
    
    # Setup embeddings model
    if not db_manager.setup_embeddings(config['embedding_model']):
        logger.error("Failed to setup embeddings model")
        return results
        
    logger.info("Embeddings model loaded successfully")
    logger.info(f"Starting to store news data for {len(news_data)} tickers")
    
    for ticker, articles in tqdm(news_data.items(), desc="Storing news data"):
        if not articles:
            logger.warning(f"No articles available for {ticker}")
            results['failed'].append(ticker)
            continue
            
        try:
            # Add embeddings to articles
            processed_articles = []
            for article in articles:
                processed_article = article.copy()
                text = article.get('summary', '') or article.get('title', '')
                
                if text:
                    try:
                        embeddings = db_manager.get_embeddings([text])
                        if embeddings is not None:
                            processed_article['embedding'] = embeddings[0].tolist()
                        else:
                            logger.warning(f"Failed to generate embedding for article: {article.get('title', 'Unknown')}")
                    except Exception as e:
                        logger.warning(f"Error generating embedding: {e}")
                        
                processed_articles.append(processed_article)
            
            # Store in database
            total_inserted = db_manager.insert_data(
                f"{news_source}", 
                processed_articles, 
                config['batch_size']
            )
            
            results['successful'].append(ticker)
            results['total_articles'] += total_inserted
            logger.info(f"Successfully stored {total_inserted} news articles for {ticker}")
            
        except Exception as e:
            logger.error(f"Failed to store news data for {ticker}: {e}")
            results['failed'].append(ticker)
    
    logger.info(f"News data storage complete: {len(results['successful'])} successful, {len(results['failed'])} failed")
    return results


def main():
    """Main pipeline."""
    config = get_config()
    logger = get_logger('SentimentDelta', config['log_level'], config['log_file'])
    
    logger.info("Starting SentimentDelta pipeline")

    # Connect to database
    db_manager = MongoDBManager(config['mongodb_uri'], config['database_name'])
    if not db_manager.connect():
        logger.error("Failed to connect to MongoDB")
        return False
    
    # news = scrape_marketwatch_ticker_news("AAPL", max_pages=2, logger=logger)
    # logger.info(news)
    
    try:
        # # Step 1: Process stock data
        # logger.info(f"Processing {len(config['tickers'])} tickers")
        # ticker_data = process_multiple_tickers(
        #     config['tickers'], 
        #     config['data_period'],
        #     config['data_interval'],
        #     logger
        # )
        
        # # Step 2: Store stock data using modular function
        # stock_results = store_stock_data(db_manager, ticker_data, config, logger)
        # logger.info(f"Stock data storage: {len(stock_results['successful'])} successful, {stock_results['total_records']} total records")
        
        # # Step 3: Fetch news data using modular function
        # news_data = fetch_news_data(config['tickers'], config['scraping_max_pages'], logger)

        # logger.info(f"Fetched news data for {len(news_data)} tickers")
        
        # # Step 4: Store news data using modular function
        # news_results = store_news_data(db_manager, news_data, config, logger, news_source="marketwatch_news")
        # logger.info(f"News data storage: {len(news_results['successful'])} successful, {news_results['total_articles']} total articles")
        
        # news = scrape_finviz_ticker_news("AAPL", logger=logger)
        # logger.info(news)

        # # Step 5: Fetch Finviz news data using modular function
        # finviz_news_data = scrape_multiple_finviz_tickers(config['tickers'], logger)
        # logger.info(f"Fetched Finviz news data for {len(finviz_news_data)} tickers")

        # # Step 6: Store Finviz news data using modular function
        # finviz_news_results = store_news_data(db_manager, finviz_news_data, config, logger, news_source="finviz_news")
        # logger.info(f"Finviz news data storage: {len(finviz_news_results['successful'])} successful, {finviz_news_results['total_articles']} total articles")

        # Step 7: Store the news data from yahoo finance
        yahoo_news_data = scrape_multiple_yahoo_tickers(config['tickers'], 0)
        logger.info(f"Fetched Yahoo news data for {len(yahoo_news_data)} tickers")
        logger.info(yahoo_news_data)
        yahoo_news_results = store_news_data(db_manager, yahoo_news_data, config, logger, news_source="yahoo_news")
        logger.info(f"Yahoo news data storage: {len(yahoo_news_results['successful'])} successful, {yahoo_news_results['total_articles']} total articles")

        return True
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return False
    
    finally:
        db_manager.disconnect()


if __name__ == "__main__":
    main()