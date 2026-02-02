from datetime import datetime, timedelta

from flask_apscheduler import APScheduler

from config.config import ApiConfig
from jobs.worker_file import (
    fetch_and_store_stock_prices,
    fetch_and_store_yahoo_news,
    fetch_and_store_finviz_news,
    process_missing_aggregates,
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
    
    Job types: 
        interval (repeats every N time)
        date (runs once at a specific time) 
        cron (runs on specific schedule)

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
        fetch_and_store_yahoo_news()

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
    # Daily aggregate calculation job, daily one time
    # -----------------------
    @scheduler.task('cron', id='daily_aggregate_calculation', hour=0, minute=0)
    def daily_aggregate_job():
        logger.info("Running daily aggregate calculation job at 12:00 AM")
        process_missing_aggregates()

    # -----------------------
    # Initial delayed fetch jobs
    # -----------------------
    @scheduler.task('date', id='initial_finviz_news_fetch', run_date=datetime.now() + timedelta(minutes=1))
    def initial_stock_fetch():
        logger.info("Running delayed initial stock price fetch after server startup")
        fetch_and_store_stock_prices()

    @scheduler.task('date', id='initial_finviz_news_fetch', run_date=datetime.now() + timedelta(minutes=1))
    def initial_finviz_news_fetch():
        logger.info("Running delayed initial Finviz news fetch after server startup")
        fetch_and_store_finviz_news()

    @scheduler.task('date', id='initial_yahoo_news_fetch', run_date=datetime.now() + timedelta(minutes=6))
    def initial_yahoo_news_fetch():
        logger.info("Running delayed initial Yahoo news fetch after server startup")
        fetch_and_store_yahoo_news()

    @scheduler.task('date', id='initial_aggregate_calculation', run_date=datetime.now() + timedelta(minutes=20))
    def initial_aggregate_calculation():
        logger.info("Running delayed initial aggregate calculation after server startup")
        process_missing_aggregates()