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

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, roc_auc_score, precision_score, recall_score, f1_score
)

from config.config import ApiConfig
from scripts.comprehensive_analysis import ComprehensiveAnalyzer

MONGO_URI = ApiConfig.MONGODB_URI
DB_NAME = ApiConfig.MONGO_DB
STOCK_PRICES_COLLECTION_NAME = "stock_prices"
AGGREGATES_COLLECTION_NAME = "aggregates"
EFT_COLLECTION_NAME = "etf"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
stock_prices_collection = db[STOCK_PRICES_COLLECTION_NAME]
aggregates_collection = db[AGGREGATES_COLLECTION_NAME]
eft_collection = db[EFT_COLLECTION_NAME]

print("Starting Consensus vs Price Impact Analysis...")

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

def load_eft_returns() -> pd.DataFrame:
    docs = list(
        eft_collection.find(
            {},
            {"ticker": 1, "date": 1, "percentage_return": 1}
        )
    )

    df = pd.DataFrame(docs)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.pivot(index="date", columns="ticker", values="percentage_return").rename(columns={
            "SPY": "spy_return",
            "XLK": "xlk_return",
            "^VIX": "vix_return"
        }).reset_index()
    df = df.dropna()

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
def merge_sentiment_price_eft(sent_df: pd.DataFrame, price_daily: pd.DataFrame, eft_df: pd.DataFrame) -> pd.DataFrame:
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

    merged = merged.merge(
        eft_df,
        on="date",
        how="left"
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
    features_a = [
        "sent_mean",
        "sent_std",
        "attention",
        "bull_bear_ratio"
    ]

    features_b = [
        "sent_mean", 
        "sent_std", 
        "attention", 
        "bull_bear_ratio",
        "spy_return",
        "xlk_return",
        "vix_return",
        "ret_lag_1",
        "ret_lag_2",
        "ret_lag_3"
    ]

    X_a = df[features_a]
    X_b = df[features_b]
    y = df["next_return"]

    model_a = Ridge(alpha=1.0)
    model_a.fit(X_a, y)
    r2_a = model_a.score(X_a, y)

    model_b = Ridge(alpha=1.0)
    model_b.fit(X_b, y)
    r2_b = model_b.score(X_b, y)

    # Compare coefficients
    print("\n=== Regression Comparison ===")
    print(f"{'Feature':20s} {'Model A coef':>12s} {'Model B coef':>12s} {'Change':>12s}")
    print("-"*60)

    reg_coef_comparison = {}
    # A +1 unit increase in [feature] on day T is associated with a [+-coef]% return on day T+1, when all other features are constant

    for f in features_a:
        coef_a = model_a.coef_[features_a.index(f)]
        coef_b = model_b.coef_[features_b.index(f)]
        change = coef_b - coef_a

        print(f"{f:20s} {coef_a:12.6f} {coef_b:12.6f} {change:12.6f}")
        reg_coef_comparison[f] = {"model_a": float(coef_a), "model_b": float(coef_b), "change": float(change)}

    print("\nR² Model A (sentiment only):", round(r2_a, 4))
    print("R² Model B (with controls):", round(r2_b, 4))

    return reg_coef_comparison, r2_a, r2_b

def find_best_threshold(probs, y_true, optimize_for="auc"):
    best_t, best_score = 0.5, -np.inf

    for t in np.linspace(0.05, 0.95, 91):
        preds = (probs >= t).astype(int)
        score = (
            f1_score(y_true, preds, zero_division=0)
            if optimize_for == "f1"
            else roc_auc_score(y_true, preds)
        )
        if score > best_score:
            best_t, best_score = t, score
    return best_t

def metrics(y_true, preds, probs):
    return {
        "accuracy": round(accuracy_score(y_true, preds), 4),
        "precision": round(precision_score(y_true, preds, zero_division=0), 4),
        "recall": round(recall_score(y_true, preds, zero_division=0), 4),
        "f1": round(f1_score(y_true, preds, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_true, probs), 4)
    }

# Logistic Regression model
def train_logistic(df: pd.DataFrame, threshold_grid = np.arange(0.4, 0.7, 0.01)):
    """
    Logistic Regression:
    Predicts probability of UP vs DOWN tomorrow.

    Output:
    P(next_return > 0 | today's sentiment)
    """
    features = [
        "sent_mean", 
        "sent_std", 
        "attention", 
        "bull_bear_ratio",
        "spy_return",
        "xlk_return",
        "vix_return",
        "ret_lag_1",
        "ret_lag_2",
        "ret_lag_3"
    ]
    X = df[features]
    y = (df["next_return"] > 0).astype(int)

    split = int(len(df) * 0.7)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
    model.fit(X_train_scaled, y_train)

    train_probs = model.predict_proba(X_train_scaled)[:, 1]
    test_probs = model.predict_proba(X_test_scaled)[:, 1]

    threshold = find_best_threshold(train_probs, y_train)

    train_preds = (train_probs >= threshold).astype(int)
    test_preds = (test_probs >= threshold).astype(int)

    logistic_metrics = {
        "threshold": threshold,
        "train": metrics(y_train, train_preds, train_probs),
        "test": metrics(y_test, test_preds, test_probs),
        "coefficients": dict(zip(features, model.coef_[0]))
    }

    print("\nBaseline probability of UP day:", round(y.mean(), 4))

    print("\n=== Logistic Regression ===")
    for k, v in logistic_metrics.items():
            print(f"{k}: {v}")
    
    return logistic_metrics

# Classification model (direction prediction)
def train_classifier(df: pd.DataFrame, threshold_grid = np.arange(0.4, 0.7, 0.01)):
    features = [
        "sent_mean", 
        "sent_std", 
        "attention", 
        "bull_bear_ratio",
        "spy_return",
        "xlk_return",
        "vix_return",
        "ret_lag_1",
        "ret_lag_2",
        "ret_lag_3"
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
        class_weight='balanced',
        random_state=42
    )

    clf.fit(X_train, y_train)

    train_probs = clf.predict_proba(X_train)[:, 1]
    test_probs = clf.predict_proba(X_test)[:, 1]

    threshold = find_best_threshold(train_probs, y_train)

    train_preds = (train_probs >= threshold).astype(int)
    test_preds = (test_probs >= threshold).astype(int)

    rf_metrics = {
        "threshold": threshold,
        "train": metrics(y_train, train_preds, train_probs),
        "test": metrics(y_test, test_preds, test_probs),
        "feature_importance": dict(
            zip(features, clf.feature_importances_)
        )
    }

    print("\n=== Random Forest Directional Prediction ===")
    for k, v in rf_metrics.items():
        print(f"{k}: {v}")

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

def run_pipeline(ticker: str, sent_df: pd.DataFrame | None = None, daily_prices: pd.DataFrame | None = None, eft_df: pd.DataFrame | None = None) -> dict:
    daily_prices = add_lagged_returns(daily_prices)

    merged = merge_sentiment_price_eft(sent_df, daily_prices, eft_df)

    print(f"\nTicker: {ticker}")
    print("Records after alignment:", len(merged))
    print("\nSample data:")
    # print(merged)

    corr_results = correlation_report(merged)
    regression_coeffs = train_regression(merged)
    logistic_metrics = train_logistic(merged)
    rf_metrics = train_classifier(merged)
    granger_pvals = run_granger(merged)
    monte_carlo_results = monte_carlo_sentiment_test(merged)
    volatility_correlation_report(merged)
    train_volatility_model(merged)
    
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
    tickers = ApiConfig.TICKERS
    all_results = {}
    
    eft_df = load_eft_returns()

    for ticker in tickers:
        try:
            print(f"\n{'='*70}")
            print(f"Processing {ticker}...")
            print(f"{'='*70}")

            sent_df = load_sentiment_aggregates(ticker)

            hourly_prices = load_hourly_prices(ticker)
            daily_prices = hourly_to_daily_targets(hourly_prices)

            all_results[ticker] = run_pipeline(ticker, sent_df, daily_prices, eft_df)
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
    
    # # Generate comprehensive analysis across all tickers
    # if all_results:
    #     print(f"\n{'='*70}")
    #     print("Generating comprehensive analysis...")
    #     print(f"{'='*70}")
    #     analyzer = ComprehensiveAnalyzer()
    #     report_info = analyzer.generate_full_report(all_results)
    #     print(f"\nAnalysis complete! Report saved to: {report_info['report_path']}")