"""Simple stock data processing."""

import logging
from typing import List, Dict, Optional
from tqdm import tqdm
import yfinance as yf
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def process_ticker_data(ticker, period="1mo", interval="1d", custom_logger=None):
    """Download and process stock data for a ticker."""
    use_logger = custom_logger or logger
    try:
        use_logger.info(f"Downloading {ticker} data: period={period}, interval={interval}")
        
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        
        if data.empty:
            use_logger.warning(f"No data returned for {ticker}")
            return None
            
        use_logger.info(f"Downloaded {len(data)} rows for {ticker}")
        
        # Simple cleanup
        data.reset_index(inplace=True)
        
        # Fix MultiIndex columns if present
        if hasattr(data.columns, 'levels'):
            # Flatten MultiIndex columns by taking the first level
            data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
        
        # Ensure all column names are strings
        data.columns = [str(col) for col in data.columns]
        
        # Clean data
        data = data.ffill().bfill().dropna()
        data['Ticker'] = ticker
        
        return data
        
    except Exception as e:
        use_logger.error(f"Error processing {ticker}: {str(e)}")
        return None


def process_multiple_tickers(tickers, period="1mo", interval="1d", custom_logger=None, start_date=None, end_date=None):
    """Process multiple tickers."""
    use_logger = custom_logger or logger
    use_logger.info(f"Starting bulk processing for {len(tickers)} tickers")
    
    results = {}
    successful = 0
    failed = 0
    
    for ticker in tqdm(tickers, desc="Processing tickers"):
        try:
            use_logger.debug(f"Starting download for {ticker}")
            
            data = process_ticker_data(ticker, period, interval, use_logger)
            results[ticker] = data
            
            if data is not None:
                successful += 1
                use_logger.info(f"Successfully processed {ticker}: {len(data)} records")
            else:
                failed += 1
                use_logger.warning(f"Failed to get data for {ticker}")
                
        except Exception as e:
            failed += 1
            use_logger.error(f"Exception processing {ticker}: {str(e)}")
            results[ticker] = None
    
    use_logger.info(f"Processing complete: successful={successful}, failed={failed}")
    
    return results