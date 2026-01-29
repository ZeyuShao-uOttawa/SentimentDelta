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

from pymongo import MongoClient
from scipy.stats import pearsonr, spearmanr
from statsmodels.tsa.stattools import grangercausalitytests

from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

from config.config import ApiConfig
from scripts.comprehensive_analysis import ComprehensiveAnalyzer

MONGO_URI = ApiConfig.MONGODB_URI
DB_NAME = ApiConfig.MONGO_DB
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

# Aggregate hourly prices to daily, calculates daily return % and range %
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

def add_lagged_returns(df: pd.DataFrame, lags: int = 3) -> pd.DataFrame:
    """
    Adds past returns as features.

    WHY:
    Prices are autocorrelated.
    If sentiment matters, it must add information
    BEYOND past price movements.
    """
    df = df.sort_values("date")
    for lag in range(1, lags + 1):
        df[f"ret_lag_{lag}"] = df["return"].shift(lag)
    return df


# Correlation between features and next day returns (If correlation is ~0 regression will be weak)
def correlation_report(df: pd.DataFrame):
    print("\n=== Correlation with next-day return ===")

    features = [
        "sent_mean",
        "sent_std",
        "attention",
        "bull_bear_ratio"
    ]

    corr_results = {}

    for col in features:
        pearson = pearsonr(df[col], df["next_return"])[0] # Pearson's measures linear dependance
        spearman = spearmanr(df[col], df["next_return"])[0] # Spearman's measures rank ordering independent of scale

        # Negative values indicate inverse correlation (Ex. When sent_mean is high price falls)
        print(f"{col:20s} Pearson={pearson: .4f}  Spearman={spearman: .4f}") # If Spearman > Pearson - Effect is nonlinear

        corr_results[col] = (float(pearson), float(spearman))
    
    return corr_results

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

    reg_coef = {}

    # A +1 unit increase in [feature] on day T is associated with a [+-coef]% return on day T+1, when all other features are constant
    print("\n=== Price Regression coefficients ===")
    for f, coef in zip(features, model.coef_):
        print(f"{f:20s} {coef: .6f}")

        reg_coef[f] = float(coef)

    return reg_coef

# Classification model
def train_logistic(df):
    """
    Logistic Regression:
    Predicts probability of UP vs DOWN tomorrow.

    Output:
    P(next_return > 0 | today's sentiment)
    """
    features = [
        "sent_mean", "sent_std", "attention", "bull_bear_ratio"
    ]

    X = df[features]
    y = (df["next_return"] > 0).astype(int)

    split = int(len(df) * 0.7)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]

    print("\n=== Logistic Regression ===")
    print("Accuracy:", round(accuracy_score(y_test, preds), 4))
    print("ROC AUC:", round(roc_auc_score(y_test, probs), 4))

    logistic_metrics = {
        "accuracy": round(accuracy_score(y_test, preds), 4),
        "auc": round(roc_auc_score(y_test, probs), 4)
    }
    
    return logistic_metrics

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

    rf_metrics = {
        "accuracy": round(accuracy_score(y_test, preds), 4),
        "auc": round(roc_auc_score(y_test, probs), 4)
    }

    return rf_metrics

def run_granger(df, max_lag=3):
    """
    Granger causality test:

    H0:
    Sentiment does NOT improve prediction of returns
    beyond past returns alone.

    If p < 0.05 → sentiment Granger-causes returns
    """
    print("\n=== Granger Causality Tests ===")

    test_df = df[["next_return", "sent_mean"]].dropna()
    test_df.columns = ["return", "sent"]

    results = grangercausalitytests(
        test_df,
        maxlag=max_lag,
        verbose=False
    )

    granger_results = {}

    for lag, res in results.items():
        pval = res[0]["ssr_ftest"][1]
        print(f"Lag {lag}: p-value = {pval:.4f}")

        granger_results[int(lag)] = float(pval)

    return granger_results

def monte_carlo_sentiment_test(
    df,
    feature="sent_mean",
    target="next_return",
    n_iter=1000
):
    """
    Monte Carlo permutation test.
    Tests whether sentiment has real predictive power.
    """

    X_real = df[[feature]].values
    y = df[target].values

    model = Ridge(alpha=1.0)
    model.fit(X_real, y)
    real_coef = model.coef_[0]

    permuted_coefs = []

    for _ in range(n_iter):
        shuffled = np.random.permutation(X_real[:, 0])
        X_perm = shuffled.reshape(-1, 1)

        model.fit(X_perm, y)
        permuted_coefs.append(model.coef_[0])

    permuted_coefs = np.array(permuted_coefs)

    p_value = np.mean(np.abs(permuted_coefs) >= np.abs(real_coef))

    print("\n=== Monte Carlo Test Results ===")
    print("Real coefficient:", round(real_coef, 6))
    print("Monte Carlo p-value:", round(p_value, 4))

    return real_coef, permuted_coefs


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

    daily_prices = hourly_to_daily_targets(hourly_prices)
    daily_prices = add_lagged_returns(daily_prices)

    merged = align_sentiment_price(sent_df, daily_prices)

    print(f"\nTicker: {ticker}")
    print("Records after alignment:", len(merged))

    corr_results = correlation_report(merged)
    regression_coeffs = train_regression(merged)
    logistic_metrics = train_logistic(merged)
    rf_metrics = train_classifier(merged)
    granger_pvals = run_granger(merged)
    volatility_correlation_report(merged)
    train_volatility_model(merged)
    monte_carlo_results = monte_carlo_sentiment_test(merged)

    # Return all results for comprehensive analysis
    return {
        'corr_results': corr_results,
        'regression_coeffs': regression_coeffs,
        'logistic_metrics': logistic_metrics,
        'rf_metrics': rf_metrics,
        'granger_pvals': granger_pvals,
        'monte_carlo': monte_carlo_results
    }

if __name__ == "__main__":
    # Option 1: Run analysis for a single ticker
    # results = run_pipeline("TSLA")
    
    # Option 2: Run analysis for multiple tickers and generate comprehensive report
    tickers = ["AAPL"]
    all_results = {}
    
    for ticker in tickers:
        try:
            print(f"\n{'='*70}")
            print(f"Processing {ticker}...")
            print(f"{'='*70}")
            all_results[ticker] = run_pipeline(ticker)
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
    
    # Generate comprehensive analysis across all tickers
    if all_results:
        print(f"\n{'='*70}")
        print("Generating comprehensive analysis...")
        print(f"{'='*70}")
        analyzer = ComprehensiveAnalyzer()
        report_info = analyzer.generate_full_report(all_results)
        print(f"\nAnalysis complete! Report saved to: {report_info['report_path']}")