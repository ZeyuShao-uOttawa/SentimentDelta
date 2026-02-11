import yfinance as yf

from pymongo import MongoClient, errors

from datetime import datetime

from config.config import ApiConfig

MONGO_URI = ApiConfig.MONGODB_URI
DB_NAME = ApiConfig.MONGO_DB
COLLECTION_NAME = "etf"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

collection.create_index([("ticker", 1), ("date", 1)], unique=True)

def fetch_yf_data(ticker, start_date, end_date):
    df = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        auto_adjust=False,
        progress=False,
        multi_level_index=False
    )

    if df.empty:
        return df

    df.reset_index(inplace=True)
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    df["percentage_return"] = df["close"].pct_change()

    return df

def store_to_mongo(df, ticker):
    for _, row in df.iterrows():
        doc = {
            "ticker": ticker,
            "date": row["date"].strftime("%Y-%m-%d"),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": int(row["volume"]),
            "percentage_return": float(row["percentage_return"]),
            "source": "yahoo",
            "updated_at": datetime.now()
        }

        try:
            collection.insert_one(doc)
        except errors.DuplicateKeyError:
            pass

def retrieve_and_store_eft(tickers, start_date, end_date):
    """
    Retrieve ETF data and store relevant information.
    
    Args:
        tickers: List of ticker symbols
        start_date: Start date (format: YYYY-MM-DD)
        end_date: End date (format: YYYY-MM-DD)
    """
    for ticker in tickers:
        df = fetch_yf_data(ticker, start_date, end_date)

        if df.empty:
            print(f"No data found for {ticker}")
            continue
        store_to_mongo(df, ticker)
        print(f"Stored data for {ticker}")

    client.close()

if __name__ == "__main__":
    start_date = "2026-01-25"
    end_date = "2026-02-05"
    tickers = ["SPY", "XLK", "^VIX"]

    retrieve_and_store_eft(tickers, start_date, end_date)