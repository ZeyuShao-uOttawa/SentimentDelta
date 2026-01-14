# SentimentDelta - Simple Stock Market Analysis

A simple, clean Python toolkit for stock data processing and news scraping. Built with simplicity in mind.

## 🚀 Features

- **Simple Design**: Clean, easy-to-understand code
- **Stock Data**: Download and process stock data from Yahoo Finance
- **News Scraping**: Scrape financial news with embeddings
- **MongoDB**: Simple database operations
- **Logging**: Consistent logging throughout (no print statements!)
- **Configurable**: Environment variable support

## 📁 Structure

```
sentiment_delta/
├── config/config.py           # Simple configuration
├── utils/
│   ├── logger.py              # Simple logging
│   └──                        # 
├── db/
│   └── database.py            # MongoDB operations
├── data/
│   ├── processor.py           # Stock data processing
│   └── scraper.py             # News scraping
└── main.py                    # Main entry point
```

## ⚡ Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MONGODB_URI="your_mongodb_uri"
export TICKERS="AAPL,GOOGL,MSFT"

# Run stock data pipeline
python main.py

# Run news scraping
python main.py scrape
```

## 🔧 Simple Usage

```python
from sentiment_delta import get_config, get_logger, create_mongodb_manager
from sentiment_delta.data import process_ticker_data

# Basic usage
config = get_config()
logger = get_logger(__name__)
data = process_ticker_data('AAPL')
logger.info(f"Got {len(data)} records for AAPL")

# Database operations
db = create_mongodb_manager(config.mongodb_uri, config.database_name)
db.create_document('my_collection', {'ticker': 'AAPL', 'price': 150})
```

## ⚙️ Configuration

| Variable      | Description             | Default              |
| ------------- | ----------------------- | -------------------- |
| `MONGODB_URI` | MongoDB connection      | Development URI      |
| `TICKERS`     | Comma-separated tickers | `AAPL,GOOGL,MSFT...` |
| `LOG_LEVEL`   | Logging level           | `INFO`               |
| `BATCH_SIZE`  | Database batch size     | `1000`               |

## 📊 What It Does

### Stock Data Pipeline

- Downloads hourly stock data for configured tickers
- Cleans and processes the data
- Stores in MongoDB (one collection per ticker)
- Logs all operations

### News Scraping Pipeline

- Scrapes financial news articles
- Extracts content and creates embeddings
- Stores in MongoDB with vector search support
- Logs progress and results

## 🎯 Key Simplifications

- **No Print Statements**: Logger everywhere for clean output
- **Simple Functions**: No complex classes, just functions
- **Minimal Config**: Just the essentials
- **Clear Logging**: Consistent logging across all modules
- **Easy Imports**: Simple module structure
- **Less Code**: Removed complexity, kept functionality

This simplified version maintains core functionality while being much easier to understand and modify!

A clean, modular Python toolkit for stock data processing and sentiment analysis. Built with DRY and KISS principles for maximum reusability and maintainability.

## 🚀 Features

- **Modular Architecture**: Clean separation of concerns with reusable components
- **Stock Data Processing**: Download and process stock data from Yahoo Finance
- **News Scraping**: Scrape financial news articles with sentiment analysis
- **MongoDB Integration**: Unified database operations with vector search support
- **Configurable Logging**: Centralized logging across all modules
- **Environment Support**: Configuration via environment variables
- **Easy Integration**: Import utilities into other projects

## 📁 Project Structure

```
sentiment_delta/
├── __init__.py                  # Main package exports
├── config/
│   ├── __init__.py
│   └── settings.py             # Configuration management
├── utils/
│   ├── __init__.py
│   ├── logger.py               # Reusable logging utility
│   └── database.py             # MongoDB operations
├── data/
│   ├── __init__.py
│   ├── processor.py            # Stock data processing
│   └── scraper.py              # News scraping
├── main.py                     # Main orchestration
├── setup.py                    # Package installation
└── requirements.txt            # Dependencies
```

## ⚡ Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

### Basic Usage

```python
# Stock data processing
from sentiment_delta.data import process_ticker_data
from sentiment_delta.config import get_config

config = get_config()
stock_data = process_ticker_data('AAPL')
```

### Configuration

Set environment variables or modify config:

```bash
export MONGODB_URI="your_mongodb_connection_string"
export TICKERS="AAPL,GOOGL,MSFT"
export LOG_LEVEL="DEBUG"
```

### Running the Pipeline

```bash
# Run stock data pipeline
python main.py

# Run news scraping pipeline
python main.py scrape
```

## 🔧 Module Usage Examples

### Configuration Management

```python
from sentiment_delta.config import get_config, create_config

# Use global config
config = get_config()
tickers = config.tickers

# Create custom config
custom_config = create_config({
    "TICKERS": ["AAPL", "GOOGL"],
    "BATCH_SIZE": 500
})
```

### Logging

```python
from sentiment_delta.utils import get_logger, log_operation_start

logger = get_logger(__name__)
log_operation_start(logger, "processing data", ticker="AAPL")
```

### Database Operations

```python
from sentiment_delta.utils import create_mongodb_manager

db_manager = create_mongodb_manager(uri, db_name)
db_manager.create_document('collection', data)
results = db_manager.vector_search('collection', 'query text')
```

### Stock Data Processing

```python
from sentiment_delta.data import process_multiple_tickers

results = process_multiple_tickers(['AAPL', 'GOOGL'])
for ticker, data in results.items():
    if data is not None:
        print(f"{ticker}: {len(data)} records")
```

### News Scraping

```python
from sentiment_delta.data import scrape_ticker_news

articles = scrape_ticker_news('AAPL', max_pages=5)
print(f"Scraped {len(articles)} articles")
```

## 🔄 Import into Other Projects

The modular design makes it easy to import utilities:

```python
# In your external project
from sentiment_delta.utils import get_logger, MongoDBManager
from sentiment_delta.data import process_ticker_data

logger = get_logger(__name__)
data = process_ticker_data('TSLA')
```

## ⚙️ Configuration Options

| Environment Variable | Description                 | Default              |
| -------------------- | --------------------------- | -------------------- |
| `MONGODB_URI`        | MongoDB connection string   | Required             |
| `DATABASE_NAME`      | Database name               | `stock_market_db`    |
| `TICKERS`            | Comma-separated ticker list | `AAPL,GOOGL,MSFT...` |
| `LOG_LEVEL`          | Logging level               | `INFO`               |
| `BATCH_SIZE`         | Database batch size         | `1000`               |
| `SCRAPING_MAX_PAGES` | Max pages per ticker        | `10`                 |

## 📊 Pipeline Outputs

### Stock Data Pipeline

- Downloads hourly stock data for configured tickers
- Stores in MongoDB collections (one per ticker)
- Creates performance indexes
- Provides execution summary

### News Scraping Pipeline

- Scrapes financial news articles
- Extracts article content and metadata
- Creates text embeddings for vector search
- Stores in MongoDB with sentiment data

## 🛠️ Key Improvements

### From Original Code:

- ✅ **Modular Structure**: Separated concerns into logical modules
- ✅ **DRY Principle**: Eliminated duplicate MongoDB and logging code
- ✅ **KISS Principle**: Simplified complex functions into smaller utilities
- ✅ **Reusable Logger**: Centralized logging configuration
- ✅ **Unified Database**: Consolidated MongoDB operations
- ✅ **Environment Config**: Support for environment variables
- ✅ **Error Handling**: Consistent error logging and handling
- ✅ **Type Hints**: Added type annotations for better code clarity
- ✅ **Documentation**: Comprehensive docstrings and examples

### Benefits:

- **Maintainability**: Easy to modify and extend individual components
- **Testability**: Each module can be tested independently
- **Reusability**: Import utilities into other projects easily
- **Scalability**: Add new data sources or processors without affecting existing code
- **Debugging**: Clear separation makes issues easier to trace

## 📝 Example Integration

```python
# example_external_project.py
import pandas as pd
from sentiment_delta import get_config, get_logger, create_mongodb_manager
from sentiment_delta.data import process_ticker_data

def my_analysis_function():
    # Setup
    config = get_config()
    logger = get_logger(__name__)

    # Get data
    data = process_ticker_data('AAPL')

    # Your analysis logic here
    analysis_result = data.describe()

    return analysis_result
```

This refactored structure provides a solid foundation for building sophisticated financial analysis tools while maintaining clean, readable, and maintainable code.
