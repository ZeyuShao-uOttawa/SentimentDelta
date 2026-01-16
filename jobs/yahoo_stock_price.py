"""Simple stock data processing."""

from logger import get_logger
from typing import List, Dict, Optional
from tqdm import tqdm
import yfinance as yf
import pandas as pd

# Configure logging

logger = get_logger(__name__)

'''
Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,y td,max 
Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo 
'''

def process_ticker_data(ticker, period="1mo", interval="15m", start=None, end=None):
    """Download and process stock data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        period: Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max (used when start/end not provided)
        interval: Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        start: Download start date string (YYYY-MM-DD), inclusive. Default is 99 years ago
        end: Download end date string (YYYY-MM-DD), exclusive. Default is now
    
    Returns:
        List of dictionaries representing stock data in JSON format with ID field (ticker_timestamp)
    """
    try:
        if start and end:
            logger.info(f"Downloading {ticker} data: start={start}, end={end}, interval={interval}")
            data = yf.download(ticker, start=start, end=end, interval=interval, progress=False)
        else:
            logger.info(f"Downloading {ticker} data: period={period}, interval={interval}")
            data = yf.download(ticker, period=period, interval=interval, progress=False)
        
        if data.empty:
            logger.warning(f"No data returned for {ticker}")
            return None
            
        logger.info(f"Downloaded {len(data)} rows for {ticker}")
        
        # Handle MultiIndex columns from yfinance
        if hasattr(data.columns, 'levels'):
            # Keep MultiIndex structure and flatten it properly
            data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
        
        # Reset index to get the datetime as a column
        data.reset_index(inplace=True)
        
        # Ensure all column names are strings
        data.columns = [str(col) for col in data.columns]
        
        # Clean data
        data = data.ffill().bfill().dropna()
        
        # Add ticker column
        data['Ticker'] = ticker
        
        # Create ID field combining ticker and timestamp
        if 'Datetime' in data.columns:
            data['_id'] = data.apply(lambda row: f"{ticker}_{pd.to_datetime(row['Datetime']).strftime('%Y%m%d_%H%M%S')}", axis=1)
        
        # Convert to JSON-friendly format
        json_data = []
        for _, row in data.iterrows():
            record = row.to_dict()
            # Convert timestamp to string if it exists
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, pd.Timestamp):
                    record[key] = value.isoformat()
            json_data.append(record)
        
        return json_data
        
    except Exception as e:
        logger.error(f"Error processing {ticker}: {str(e)}")
        return None