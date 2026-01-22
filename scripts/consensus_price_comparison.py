"""
Consensus vs Price Impact Analysis

This script:
1. Aggregates hourly prices into daily bars
2. Aligns daily sentiment consensus with next-day price movement
3. Computes correlation statistics
4. Trains regression and classification models
"""

import pandas as pd
import numpy as np

from scipy.stats import pearsonr, spearmanr
from pymongo import MongoClient
from datetime import datetime, timedelta

from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI_MEET", "mongodb://mongo:27017")
DB_NAME = "stock_market_db"
STOCK_PRICES_COLLECTION_NAME = "stock_prices"
AGGREGATES_COLLECTION_NAME = "aggregates"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
stock_prices_collection = db[STOCK_PRICES_COLLECTION_NAME]
aggregates_collection = db[AGGREGATES_COLLECTION_NAME]

def load_sentiment_aggregates(ticker: str) -> pd.DataFrame:
    docs = list(
        aggregates_collection.find(
            {"ticker": ticker},
            {"_id": 0}
        )
    )

    df = pd.DataFrame(docs)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df

def load_hourly_prices(ticker: str) -> pd.DataFrame:
    docs = list(
        stock_prices_collection.find(
            {"Ticker": ticker},
            {"_id": 0}
        )
    )

    df = pd.DataFrame(docs)
    df["Datetime"] = pd.to_datetime(df["Datetime"])
    return df

# Aggregate hourly prices to daily
def hourly_to_daily_targets(price_df: pd.DataFrame) -> pd.DataFrame:
    price_df = price_df.copy()
    price_df["date"] = price_df["Datetime"].dt.date

    daily = price_df.groupby(["Ticker", "date"]).agg(
        open=("Open", "first"),
        close=("Close", "last"),
        high=("High", "max"),
        low=("Low", "min"),
        volume=("Volume", "sum"),
    ).reset_index()

    daily["return"] = (daily["close"] - daily["open"]) / daily["open"]
    daily["range"] = (daily["high"] - daily["low"]) / daily["open"]

    return daily

# Shifts prices to next day prices to see results of sentiment
def align_sentiment_price(sent_df: pd.DataFrame, price_daily: pd.DataFrame) -> pd.DataFrame:
    sent_df = sent_df.copy()
    sent_df["date"] = pd.to_datetime(sent_df["date"]).dt.date
    sent_df = sent_df.rename(columns={"ticker": "Ticker"})

    price_daily = price_daily.sort_values(["Ticker", "date"])
    price_daily["next_return"] = price_daily.groupby("Ticker")["return"].shift(-1)
    price_daily["next_range"] = price_daily.groupby("Ticker")["range"].shift(-1)

    merged = sent_df.merge(
        price_daily,
        on=["Ticker", "date"],
        how="inner"
    )

    merged = merged.dropna(subset=["next_return", "next_range"])
    return merged

# Correlation between features and next day returns (If correlation is ~0 regression will be weak)
def correlation_report(df: pd.DataFrame):
    print("\n=== Correlation with next-day return ===")

    features = [
        "sent_mean",
        "sent_std",
        "attention",
        "bull_bear_ratio"
    ]

    for col in features:
        pearson = pearsonr(df[col], df["next_return"])[0] # Pearson's measures linear dependance
        spearman = spearmanr(df[col], df["next_return"])[0] # Spearman's measures rank ordering independent of scale

        # Negative values indicate inverse correlation (Ex. When sent_mean is high price falls)
        print(f"{col:20s} Pearson={pearson: .4f}  Spearman={spearman: .4f}") # If Spearman > Pearson - Effect is nonlinear

# Regression model (impact strength) "How much does each sentiment variable move next-day returns, holding the others constant?"
def train_regression(df: pd.DataFrame):
    features = [
        "sent_mean",
        "sent_std",
        "attention",
        "bull_bear_ratio"
    ]

    X = df[features]
    y = df["next_return"]

    model = Ridge(alpha=1.0)
    model.fit(X, y)

    # A +1 unit increase in [feature] on day T is associated with a [+-coef]% return on day T+1, when all other features are constant
    print("\n=== Price Regression coefficients ===")
    for f, coef in zip(features, model.coef_):
        print(f"{f:20s} {coef: .6f}")

    return model

# Classification model (direction prediction)
def train_classifier(df: pd.DataFrame):
    features = [
        "sent_mean",
        "sent_std",
        "attention",
        "bull_bear_ratio"
    ]

    X = df[features]
    y = (df["next_return"] > 0).astype(int)

    split_idx = int(len(df) * 0.7)  # time-aware split

    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    # Use Random Forest to capture non linear interactions
    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=5,
        random_state=42
    )

    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    probs = clf.predict_proba(X_test)[:, 1]

    print("\n=== Directional prediction ===")
    print("Accuracy:", round(accuracy_score(y_test, preds), 4))
    print("ROC AUC:", round(roc_auc_score(y_test, probs), 4))

    return clf

def volatility_correlation_report(df: pd.DataFrame):
    print("\n=== Correlation with next-day range ===")

    features = [
        "sent_mean",
        "sent_std",
        "attention",
        "bull_bear_ratio"
    ]

    for col in features:
        pearson = pearsonr(df[col], df["next_range"])[0]
        spearman = spearmanr(df[col], df["next_range"])[0]
        print(f"{col:20s} Pearson={pearson: .4f}  Spearman={spearman: .4f}")

def train_volatility_model(df: pd.DataFrame):
    features = [
        "sent_mean", 
        "sent_std", 
        "attention", 
        "bull_bear_ratio"
    ]

    X = df[features]
    y = df["next_range"]

    model = Ridge(alpha=1.0)
    model.fit(X, y)

    print("\n=== Volatility Regression coefficients ===")
    for f, coef in zip(features, model.coef_):
        print(f"{f:20s} {coef: .6f}")

    return model

def run_pipeline(ticker: str):
    sent_df = load_sentiment_aggregates(ticker)
    hourly_prices = load_hourly_prices(ticker)

    daily_price = hourly_to_daily_targets(hourly_prices)
    merged = align_sentiment_price(sent_df, daily_price)

    print(f"\nTicker: {ticker}")
    print("Records after alignment:", len(merged))

    correlation_report(merged)
    train_regression(merged)
    train_classifier(merged)
    train_volatility_model(merged)

if __name__ == "__main__":
    run_pipeline("TSLA")