from routes.api import api
from routes.news import news_bp
from routes.health import health_bp

api.register_blueprint(news_bp)
api.register_blueprint(health_bp)