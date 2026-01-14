from routes.api import api
from routes.news import news_bp

api.register_blueprint(news_bp)