from pymongo import MongoClient
from datetime import datetime
from collections import Counter
import math
import numpy as np

def all_scores(docs):
    return [d["sentiment"]["score"] for d in docs]


# Average sentiment score (High = Bullish | 0 = Neutral | Low = Bearish)
def sentiment_mean(docs):
    scores = all_scores(docs)

    sent_mean = np.mean(scores) if scores else 0.0

    return sent_mean

# Standard deviation of scores (High = Agreement | Low = Disagreement)
def sentiment_std(docs):
    scores = all_scores(docs)

    sent_std = np.std(scores) if len(scores) > 1 else 0.0

    return sent_std

# Attention count of total articles (High = Consensus Has Weight | Low = Consensus Might Not Matter)
def sentiment_attention(docs):
    att = len(docs)

    return att

def sentiment_bull_bear_ratio(docs):
    bullish = sum(1 for d in docs if d["sentiment"]["score"] > 0)
    bearish = sum(1 for d in docs if d["sentiment"]["score"] < 0)

    bull_bear_ratio = bullish / (bearish + 1)

    return bull_bear_ratio

def daily_aggregate(docs):

    sent_mean = sentiment_mean(docs)
    sent_std = sentiment_mean(docs)
    att = sentiment_attention(docs)
    bull_bear_ratio = sentiment_bull_bear_ratio(docs)

    features = {
        "sent_mean": sent_mean,
        "sent_std": sent_std,
        "attention": att,
        "bull_bear_ratio": bull_bear_ratio
    }

    return features