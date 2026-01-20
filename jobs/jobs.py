from datetime import datetime, timedelta

from flask_apscheduler import APScheduler

from config.config import ApiConfig
from jobs.worker_file import (
    fetch_and_store_stock_prices,
    fetch_and_store_stock_news,
    fetch_and_store_finviz_news,
)
from logger import get_logger


logger = get_logger(__name__)


def setup_scheduler(app):
    """
    Initialize and configure the APScheduler with the Flask app.
    
    Args:
        app: Flask application instance.
        
    Returns:
        APScheduler instance.
    """
    scheduler = APScheduler()
    scheduler.init_app(app)

    # Register all scheduled jobs
    register_jobs(scheduler)

    scheduler.start()
    return scheduler


def register_jobs(scheduler):
    """
    Register all scheduled jobs with the APScheduler instance.
    
    Args:
        scheduler: APScheduler instance.
    """
    fetch_interval_hours = ApiConfig.STOCK_FETCH_INTERVAL_HOURS

    # -----------------------
    # Health check job
    # -----------------------
    @scheduler.task('interval', id='health_check', minutes=30)
    def health_check_job():
        logger.info("Scheduler health check - system running normally")

    # -----------------------
    # Stock price fetching job
    # -----------------------
    @scheduler.task('interval', id='stock_price_fetcher', hours=fetch_interval_hours)
    def stock_price_job():
        logger.info(
            f"Running scheduled stock price fetch job (every {fetch_interval_hours} hours)"
        )
        fetch_and_store_stock_prices()

    # -----------------------
    # Stock news fetching job
    # -----------------------
    @scheduler.task('interval', id='stock_news_fetcher', hours=fetch_interval_hours)
    def stock_news_job():
        logger.info(
            f"Running scheduled stock news fetch job (every {fetch_interval_hours} hours)"
        )
        fetch_and_store_stock_news()

    # -----------------------
    # Finviz news fetching job
    # -----------------------
    @scheduler.task('interval', id='finviz_news_fetcher', hours=fetch_interval_hours)
    def finviz_news_job():
        logger.info(
            f"Running scheduled Finviz news fetch job (every {fetch_interval_hours} hours)"
        )
        fetch_and_store_finviz_news()

    # -----------------------
    # Initial delayed fetch jobs
    # -----------------------
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