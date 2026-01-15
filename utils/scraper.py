"""Simple web scraping for financial news."""

import time
import random
import logging
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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


def get_article_text(url):
    """Extract article text."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text if article.text and len(article.text) > 50 else None
    except:
        return None


def scrape_marketwatch_ticker_news(ticker, max_pages=5, custom_logger=None):
    """Scrape news for a ticker."""
    use_logger = custom_logger or logger
    use_logger.info(f"Starting MarketWatch scrape for {ticker} with {max_pages} pages")
    
    session = get_session()
    articles = []
    
    for page in range(max_pages):
        try:
            url = f"{MARKETWATCH_BASE_URL}/investing/stock/{ticker.lower()}/moreheadlines?channel=AllDowJones&source=ChartingSymbol"
            if page > 0:
                url += f"&pageNumber={page}"
            
            # Add random delay before request
            time.sleep(random.uniform(1, 3))
            
            response = session.get(url, timeout=30)

            # Status of the page response
            use_logger.info(f"Scraping {ticker} page {page} - URL Status Code: {response.status_code}")

            if response.status_code == 401:
                use_logger.warning(f"Access denied (401) for {ticker} page {page}. Trying with new session...")
                # Try with a new session and different user agent
                session = get_session()
                time.sleep(random.uniform(3, 7))
                response = session.get(url, timeout=30)
                use_logger.info(f"Retry attempt - Status Code: {response.status_code}")
            
            if response.status_code != 200:
                use_logger.warning(f"Failed to access page {page} for {ticker} (Status: {response.status_code})")
                break
            
            soup = BeautifulSoup(response.content, 'html.parser')
            container = soup.find('div', class_='collection__elements j-scrollElement')
            if not container:
                break
            
            elements = container.find_all('div', class_=lambda x: x and 'element--article' in x)
            page_articles = []
            
            for element in tqdm(elements, desc=f"Processing {ticker} articles page {page}", leave=False):
                # Find headline
                headline_elem = element.select_one('h3 a, h2 a')
                if not headline_elem:
                    continue
                
                title = headline_elem.get_text(strip=True)
                if not title or len(title) < 10:
                    continue
                
                article_url = headline_elem.get('href')
                if not article_url:
                    continue
                
                if not article_url.startswith('http'):
                    article_url = f"{MARKETWATCH_BASE_URL}{article_url}"
                
                # Extract timestamp information
                timestamp = None
                
                # Try to get timestamp from data-est attribute
                timestamp_elem = element.find('span', class_='article__timestamp')
                if timestamp_elem:
                    timestamp = timestamp_elem.get('data-est')
                
                # If not found, try to get from the element itself
                if not timestamp:
                    timestamp = element.get('data-timestamp')
                
                # Get article content
                content = get_article_text(article_url)
                
                article_data = {
                    'ticker': ticker.upper(),
                    'title': title,
                    'url': article_url,
                    'summary': content or 'Content unavailable',
                    'source': 'MarketWatch'
                }
                
                # Add timestamp information if available
                if timestamp:
                    article_data['timestamp'] = timestamp
                
                page_articles.append(article_data)
            
            articles.extend(page_articles)
            use_logger.info(f"Page {page}: {len(page_articles)} articles scraped for {ticker}")
            
            if not page_articles:
                break
                
            # Longer delay between pages to be respectful
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            use_logger.error(f"Error scraping page {page} for {ticker}: {e}")
            break
    
    use_logger.info(f"MarketWatch scraping complete for {ticker}: {len(articles)} articles")
    
    return articles

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
                content = None
                if article_url and article_url.startswith('http'):
                    try:
                        content = get_article_text(article_url)
                    except:
                        pass
                
                article_data = {
                    'ticker': ticker.upper(),
                    'title': title,
                    'url': article_url or 'N/A',
                    'summary': content or 'Content unavailable',
                    'source': source,
                    'parsed_datetime': parsed_datetime.isoformat() if parsed_datetime else None,
                    'timestamp': int(parsed_datetime.timestamp() * 1000) if parsed_datetime else None
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



def scrape_multiple_marketwatch_tickers(tickers, max_pages=5, custom_logger=None):
    """Scrape multiple tickers."""
    use_logger = custom_logger or logger
    use_logger.info(f"Starting bulk MarketWatch scrape for {len(tickers)} tickers")
    
    results = {}
    for ticker in tqdm(tickers, desc="Scraping MarketWatch tickers"):
        results[ticker] = scrape_marketwatch_ticker_news(ticker, max_pages, use_logger)
        use_logger.info(f"Completed MarketWatch scraping for {ticker}: {len(results[ticker])} articles")
        # Longer delay between tickers to avoid rate limiting
        time.sleep(random.uniform(5, 10))
    
    total_articles = sum(len(articles) for articles in results.values())
    use_logger.info(f"Bulk MarketWatch scrape completed: {total_articles} total articles from {len(tickers)} tickers")
    return results


def scrape_multiple_finviz_tickers(tickers, custom_logger=None):
    """Scrape multiple tickers from Finviz."""
    use_logger = custom_logger or logger
    use_logger.info(f"Starting bulk Finviz scrape for {len(tickers)} tickers")
    
    results = {}
    for ticker in tqdm(tickers, desc="Scraping Finviz tickers"):
        results[ticker] = scrape_finviz_ticker_news(ticker, use_logger)
        use_logger.info(f"Completed Finviz scraping for {ticker}: {len(results[ticker])} articles")
        # Longer delay between tickers to avoid rate limiting
        time.sleep(random.uniform(5, 10))
    
    total_articles = sum(len(articles) for articles in results.values())
    use_logger.info(f"Bulk Finviz scrape completed: {total_articles} total articles from {len(tickers)} tickers")
    return results