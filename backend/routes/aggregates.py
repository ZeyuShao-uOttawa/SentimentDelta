"""HTTP routes for aggregate documents.

Exposes endpoints to create single/multiple aggregate documents, query
by ticker/date/range, fetch latest, list available aggregate dates,
and perform updates/deletes by id or by ticker+date.
"""

from flask import Blueprint, request, jsonify
from bson import ObjectId
from utils.logger import get_logger
from db.aggregates_queries import (
    create_aggregate,
    get_aggregate_by_id,
    get_all_aggregates,
    get_aggregates_by_ticker,
    get_aggregates_by_ticker_and_date,
    get_aggregate_date_range,
    get_latest_aggregate_by_ticker,
    get_aggregate_dates,
)

# Logger for this module
logger = get_logger(__name__)

# Blueprint to register aggregate-related routes
aggregates_bp = Blueprint("aggregates", __name__)


def _serialize_doc(doc: dict) -> dict:
    """Serialize aggregate document for JSON responses.

    Convert ObjectId instances (and the top-level "_id") to strings so they
    can be JSON-encoded. Non-dict values are returned unchanged.
    """
    if not isinstance(doc, dict):
        return doc
    out = {}
    for k, v in doc.items():
        # Convert the MongoDB primary key to string
        if k == "_id":
            out[k] = str(v)
            continue
        # Convert any nested ObjectId values to string if present
        try:
            if isinstance(v, ObjectId):
                out[k] = str(v)
                continue
        except Exception:
            # Be permissive: if isinstance check errors, fall back to raw value
            pass
        out[k] = v
    return out
    
@aggregates_bp.route("/aggregates", methods=["GET"])
def list_aggregates():
    """List aggregates with optional `limit` query param.

    Query params:
    - limit: optional int to cap returned documents (default 100)
    """
    limit = request.args.get("limit")
    try:
        limit_val = int(limit) if limit else 100
    except ValueError:
        return jsonify({"error": "invalid limit"}), 400

    # Fetch documents and serialize for JSON response
    docs = get_all_aggregates(limit_val)
    return jsonify({"count": len(docs), "data": [_serialize_doc(d) for d in docs]}), 200


@aggregates_bp.route("/aggregates/id/<doc_id>", methods=["GET"])
def get_aggregate(doc_id: str):
    """Fetch an aggregate document by its `_id`.

    Returns 400 for invalid id format, 404 if not found.
    """
    try:
        doc = get_aggregate_by_id(doc_id)
    except Exception:
        # Underlying query may raise on bad ObjectId conversion
        return jsonify({"error": "invalid id"}), 400
    if not doc:
        return jsonify({"error": "not_found"}), 404
    return jsonify(_serialize_doc(doc)), 200


@aggregates_bp.route("/aggregates/ticker/<ticker>", methods=["GET"])
def get_aggregates_for_ticker(ticker: str):
    """Return aggregates for a ticker.

    Behavior:
    - If `start` and `end` query params present -> return date range
    - Else if `date` param present -> return aggregates for that date
    - Otherwise -> return all aggregates for ticker
    """
    start = request.args.get("start")
    end = request.args.get("end")
    date = request.args.get("date")
    ticker_up = ticker.upper()

    # Route to the appropriate query helper based on provided params
    if start and end:
        docs = get_aggregate_date_range(ticker_up, start, end)
    elif date:
        docs = get_aggregates_by_ticker_and_date(ticker_up, date)
    else:
        docs = get_aggregates_by_ticker(ticker_up)

    return jsonify({"ticker": ticker_up, "count": len(docs), "data": [_serialize_doc(d) for d in docs]}), 200


@aggregates_bp.route("/aggregates/ticker/<ticker>/latest", methods=["GET"])
def get_latest_aggregate(ticker: str):
    """Return the latest aggregate for a ticker.

    Returns 404 if none found.
    """
    doc = get_latest_aggregate_by_ticker(ticker.upper())
    if not doc:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"ticker": ticker.upper(), "latest": _serialize_doc(doc)}), 200


@aggregates_bp.route("/aggregates/dates", methods=["GET"])
def list_aggregate_dates():
    """Return list of aggregate date strings; optional `ticker` param.

    Query params:
    - ticker: optional ticker to filter dates for that symbol
    """
    ticker = request.args.get("ticker")
    dates = get_aggregate_dates(ticker.upper() if ticker else None)
    return jsonify({"count": len(dates), "dates": dates}), 200
