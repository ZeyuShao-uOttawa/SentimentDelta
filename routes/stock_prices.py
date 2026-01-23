from flask import request, jsonify, Blueprint
from db.stock_price_queries import (
    get_stock_data_by_range,
    get_latest_stock_data,
    get_all_stock_tickers,
    get_ticker_date_range,
)
from utils.logger import get_logger
from datetime import datetime, timedelta
from bson import ObjectId
import pandas as pd

stock_prices_bp = Blueprint("stock_prices", __name__)
logger = get_logger(__name__)


def _serialize_doc(doc: dict) -> dict:
    """Convert a DB document into JSON-serializable primitives.

    This converts `_id` and `ObjectId` to strings and pandas/`datetime`
    timestamps to ISO-8601 strings so responses can be JSON-encoded.
    """
    if not isinstance(doc, dict):
        return doc

    out = {}
    for k, v in doc.items():
        if k == "_id":
            out[k] = str(v)
            continue

        # pandas Timestamp
        if isinstance(v, pd.Timestamp):
            out[k] = v.isoformat()
            continue

        # datetime
        if isinstance(v, datetime):
            out[k] = v.isoformat()
            continue

        # ObjectId or other objects
        try:
            if isinstance(v, ObjectId):
                out[k] = str(v)
                continue
        except Exception:
            pass

        out[k] = v

    return out


@stock_prices_bp.route("/stock_prices/tickers", methods=["GET"])
def list_tickers():
    """Return a list of unique tickers available in the collection."""

    tickers = get_ticker_date_range()
    return jsonify({"tickers": tickers}), 200


@stock_prices_bp.route("/stock_prices/<ticker>", methods=["GET"])
def get_prices(ticker: str):
    """Fetch historical price records for `ticker`.

    Optional query params: `start` and `end` as ISO date strings to
    filter the returned range.
    """

    start = request.args.get("start")
    end = request.args.get("end")

    # If no dates are provided, default to the last 3 days
    if not start and not end:
        now = datetime.utcnow()
        end = now.isoformat()
        start = (now - timedelta(days=3)).isoformat()

    results = get_stock_data_by_range(ticker.upper(), start, end)
    serialized = [_serialize_doc(r) for r in results]
    return jsonify({"ticker": ticker.upper(), "count": len(serialized), "data": serialized}), 200


@stock_prices_bp.route("/stock_prices/<ticker>/latest", methods=["GET"])
def get_latest(ticker: str):
    """Return the latest available price record for `ticker`."""

    doc = get_latest_stock_data(ticker.upper())
    if not doc:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"ticker": ticker.upper(), "latest": _serialize_doc(doc)}), 200
