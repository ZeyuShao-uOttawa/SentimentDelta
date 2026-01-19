"""Simple web scraping for financial news."""

import time
import random
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from utils.scraper import get_article_text
from logger import get_logger

# Configure logging
logger = get_logger(__name__)

MARKETWATCH_BASE_URL = "https://www.marketwatch.com"
FINVIZ_BASE_URL = "https://finviz.com"

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
]


def get_session():
    """Get a requests session with realistic browser headers."""
    session = requests.Session()
    
    # Set realistic headers to avoid detection
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Charset': 'utf-8, iso-8859-1;q=0.5',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1'
    }
    
    session.headers.update(headers)
    return session


def scrape_finviz_ticker_news(ticker, custom_logger=None):
    """Scrape news for a ticker from Finviz."""
    use_logger = custom_logger or logger
    use_logger.info(f"Starting Finviz scrape for {ticker}")
    
    session = get_session()
    articles = []
    
    try:
        url = f"{FINVIZ_BASE_URL}/quote.ashx?t={ticker.upper()}"
        
        # Add random delay before request
        time.sleep(random.uniform(1, 3))
        
        response = session.get(url, timeout=30)
        
        use_logger.info(f"Finviz scraping {ticker} - Status Code: {response.status_code}")
        
        if response.status_code != 200:
            use_logger.warning(f"Failed to access Finviz for {ticker} (Status: {response.status_code})")
            return articles
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the news table
        news_table = soup.find('table', {'id': 'news-table', 'class': 'fullview-news-outer news-table'})
        
        if not news_table:
            use_logger.warning(f"No news table found for {ticker} on Finviz")
            return articles
        
        # Find all news rows
        rows = news_table.find('tbody').find_all('tr') if news_table.find('tbody') else news_table.find_all('tr')
        
        # Track the current date for parsing time-only entries
        current_date = datetime.now().date()
        last_full_date = None
        
        for row in tqdm(rows, desc=f"Processing {ticker} news", leave=False):
            # Progress tracking
            use_logger.debug(f"Processing row {rows.index(row) + 1} of {len(rows)} for {ticker}")
            try:
                # Get timestamp from first td
                time_cell = row.find('td', {'width': '130'})
                if not time_cell:
                    continue
                
                raw_timestamp = time_cell.get_text(strip=True)
                parsed_datetime = None
                formatted_time = raw_timestamp
                
                # Parse different timestamp formats
                try:
                    if 'Today' in raw_timestamp:
                        # Format: "Today 04:24PM"
                        time_part = raw_timestamp.replace('Today', '').strip()
                        time_obj = datetime.strptime(time_part, '%I:%M%p').time()
                        parsed_datetime = datetime.combine(current_date, time_obj)
                        last_full_date = current_date
                        formatted_time = f"Today {time_part}"
                        
                    elif re.match(r'^\d{2}:\d{2}[AP]M$', raw_timestamp):
                        # Format: "04:24PM" - use last known date
                        time_obj = datetime.strptime(raw_timestamp, '%I:%M%p').time()
                        if last_full_date:
                            parsed_datetime = datetime.combine(last_full_date, time_obj)
                        else:
                            parsed_datetime = datetime.combine(current_date, time_obj)
                        formatted_time = raw_timestamp
                        
                    elif re.match(r'[A-Z][a-z]{2}-\d{2}-\d{2}', raw_timestamp):
                        # Format: "Jan-11-26 09:31PM"
                        if ' ' in raw_timestamp:
                            date_part, time_part = raw_timestamp.split(' ', 1)
                            # Parse date like "Jan-11-26"
                            month_day_year = date_part.split('-')
                            if len(month_day_year) == 3:
                                month_str, day_str, year_str = month_day_year
                                # Convert 2-digit year to 4-digit
                                year = 2000 + int(year_str) if int(year_str) < 50 else 1900 + int(year_str)
                                month = datetime.strptime(month_str, '%b').month
                                day = int(day_str)
                                
                                time_obj = datetime.strptime(time_part, '%I:%M%p').time()
                                parsed_datetime = datetime.combine(datetime(year, month, day).date(), time_obj)
                                last_full_date = parsed_datetime.date()
                                formatted_time = raw_timestamp
                        
                    else:
                        # Handle other formats or keep raw
                        formatted_time = raw_timestamp
                        
                except Exception as e:
                    use_logger.debug(f"Could not parse timestamp '{raw_timestamp}' for {ticker}: {e}")
                    formatted_time = raw_timestamp
                
                # Get news content from second td
                content_cell = row.find('td', {'align': 'left'})
                if not content_cell:
                    continue
                
                # Find the news link container
                news_container = content_cell.find('div', class_='news-link-container')
                if not news_container:
                    continue
                
                # Extract title and URL from news-link-left
                link_left = news_container.find('div', class_='news-link-left')
                if not link_left:
                    continue
                
                news_link = link_left.find('a', class_='tab-link-news')
                if not news_link:
                    continue
                
                title = news_link.get_text(strip=True)
                article_url = news_link.get('href', '')
                
                # Extract source from news-link-right
                source = 'Finviz'
                
                # Handle relative URLs
                if article_url and not article_url.startswith('http'):
                    article_url = f"{FINVIZ_BASE_URL}{article_url}"
                
                # Skip if essential data is missing
                if not title or len(title) < 10:
                    continue
                
                # Get article content (optional - can be slow)
                # content = None
                # if article_url and article_url.startswith('http'):
                #     try:
                #         content = get_article_text(article_url)
                #     except:
                #         pass
                
                article_data = {
                    'ticker': ticker.upper(),
                    'title': title,
                    'url': article_url or 'N/A',
                    'source': source,
                    'date': parsed_datetime.strftime('%Y-%m-%d') if parsed_datetime else None,
                    'timestamp': int(parsed_datetime.timestamp() * 1000) if parsed_datetime else None,
                }
                
                articles.append(article_data)
                
                # Small delay between article processing
                time.sleep(random.uniform(0.1, 0.3))
                
            except Exception as e:
                use_logger.warning(f"Error processing news row for {ticker}: {e}")
                continue
        
        use_logger.info(f"Finviz scraping complete for {ticker}: {len(articles)} articles found")
        
    except Exception as e:
        use_logger.error(f"Error scraping Finviz for {ticker}: {e}")
    
    return articles