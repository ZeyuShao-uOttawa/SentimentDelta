from flask_apscheduler import APScheduler
from logger import get_logger

logger = get_logger(__name__)

def setup_scheduler(app):
    """Initialize and configure the scheduler with the Flask app"""
    scheduler = APScheduler()
    scheduler.init_app(app)
    
    # Register all scheduled jobs
    register_jobs(scheduler)
    
    scheduler.start()
    return scheduler

def register_jobs(scheduler):
    """Register all scheduled jobs"""
    
    @scheduler.task('interval', id='printJob', seconds=30)
    def printJob():
        logger.info("Job 1 executed every 30 seconds")
        print("Job 1 executed every 30 seconds")
    
    # Add more jobs here as needed
    # @scheduler.task('cron', id='daily_job', hour=0, minute=0)
    # def daily_job():
    #     logger.info("Daily job executed")
    #     print("Daily job executed")