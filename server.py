from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from config.config import ApiConfig
from utils.logger import get_logger
from db.database import MongoDBManager
from routes import api
import atexit

def create_app():
    app = Flask(__name__)
    CORS(app)

    logger = get_logger('SentimentDeltaAPI', ApiConfig.LOG_LEVEL, ApiConfig.LOG_FILE)

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

    app.register_blueprint(api)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)