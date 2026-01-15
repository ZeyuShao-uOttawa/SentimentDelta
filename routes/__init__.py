"""
Routes package for SentimentDelta API
"""
from .health import health_bp

# Export all blueprints
__all__ = ['health_bp']