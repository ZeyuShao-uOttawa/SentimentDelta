"""Register route blueprints on the API root blueprint.

This module centralizes registering sub-blueprints so they are exposed
under the `/api/v1` prefix defined in `routes/api.py`.
"""

from routes.api import api
from routes.news import news_bp
from routes.health import health_bp
from routes.stock_prices import stock_prices_bp

api.register_blueprint(news_bp)
api.register_blueprint(health_bp)
api.register_blueprint(stock_prices_bp)