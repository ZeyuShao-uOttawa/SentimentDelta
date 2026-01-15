import atexit
from flask import Flask
from flask_cors import CORS
from db.database import MongoDBManager
from logger import get_logger
from jobs import setup_scheduler
from routes import api
from config.config import ApiConfig


def create_app():
    app = Flask(__name__)
    CORS(app)
    logger = get_logger(__name__)
    logger.info("Starting SentimentDelta API server...")

    db_manager = MongoDBManager(ApiConfig.MONGO_URI, ApiConfig.MONGO_DB)

    if not db_manager.connect():
        logger.error("Failed to connect to MongoDB")

    if not db_manager.setup_embeddings(ApiConfig.EMBEDDING_MODEL):
        logger.error("Failed to setup embeddings model")

    app.db_manager = db_manager

    @atexit.register
    def shutdown_db():
        logger.info("Shutting down MongoDB connection")
        db_manager.disconnect()
    
    # Setup scheduler and jobs
    setup_scheduler(app)
    
    # Standard blueprint registration
    app.register_blueprint(api)
    
    return app

if __name__ == '__main__':
    app = create_app()
    # Note: app.run() only starts the web server, NOT the cron jobs.
    # The cron jobs are run by the system cron daemon independently.
    app.run(debug=False, host='0.0.0.0', port=3000)
