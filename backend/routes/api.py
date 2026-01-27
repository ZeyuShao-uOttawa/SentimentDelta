"""API blueprint root for versioned routes.

All route blueprints should be registered on the `api` blueprint so they
are exposed under `/api/v1/...`.
"""

from flask import Blueprint

api = Blueprint("api", __name__, url_prefix="/api/v1")