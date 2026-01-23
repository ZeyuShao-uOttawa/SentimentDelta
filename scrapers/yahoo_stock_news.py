"""
Yahoo Finance News Scraper - Functional version
Scrapes news articles from Yahoo Finance with infinite scroll.
"""

import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from logger import get_logger

logger = get_logger(__name__)

BASE_URL = "https://ca.finance.yahoo.com/quote/{symbol}/news/"

TIME_PATTERNS = {
    'days': [r'(\d+)d ago', r'(\d+)\s*days?\s*ago'],
    'hours': [r'(\d+)\s*hrs?\s*ago', r'(\d+)\s*hours?\s*ago'],
    'minutes': [r'(\d+)\s*mins?\s*ago', r'(\d+)\s*minutes?\s*ago']
}


def create_driver(headless: bool = True) -> webdriver.Chrome:
    """Create optimized Chrome driver."""
    logger.info(f"Creating Chrome driver (headless={headless})")
    
    options = Options()
    
    # Essential options only
    essential_args = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--window-size=1920,1080",
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "--disable-blink-features=AutomationControlled",  # Avoid detection
    ]
    
    if headless:
        essential_args.append("--headless=new")

    for arg in essential_args:
        options.add_argument(arg)

    # Reduce noisy chrome logs
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())

    # Try creating driver; if it fails, retry with non-headless for debugging
    try:
        driver = webdriver.Chrome(service=service, options=options)
        # Optimized timeouts
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(10)
        logger.info("Chrome driver created successfully")
        return driver
    except Exception as e:
        logger.warning(f"Initial driver creation failed: {e}. Retrying non-headless once...")
        try:
            opts2 = Options()
            opts2.add_argument("--window-size=1920,1080")
            opts2.add_argument("--user-agent=Mozilla/5.0 (Macintosh)")
            opts2.add_experimental_option("excludeSwitches", ["enable-logging"])
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=opts2)
            driver.set_page_load_timeout(60)
            driver.implicitly_wait(10)
            logger.info("Chrome driver created successfully on retry (non-headless)")
            return driver
        except Exception as e2:
            logger.error(f"Failed to create Chrome driver on retry: {e2}")
            raise


def parse_relative_time(time_text: str) -> str:
    """Convert relative time string to yyyy-mm-dd format."""
    now = datetime.now()
    time_text = time_text.lower().strip()
    
    for pattern in TIME_PATTERNS['days']:
        if match := re.search(pattern, time_text):
            days = int(match.group(1))
            return (now - timedelta(days=days)).strftime('%Y-%m-%d')
    
    for pattern in TIME_PATTERNS['hours']:
        if match := re.search(pattern, time_text):
            hours = int(match.group(1))
            return (now - timedelta(hours=hours)).strftime('%Y-%m-%d')
    
    for pattern in TIME_PATTERNS['minutes']:
        if match := re.search(pattern, time_text):
            minutes = int(match.group(1))
            return (now - timedelta(minutes=minutes)).strftime('%Y-%m-%d')
    
    return now.strftime('%Y-%m-%d')


def check_target_reached(html: str, target_days: int) -> bool:
    """Check if we've scrolled to target days ago content."""
    if target_days == 0:
        return bool(re.search(r'1\s*d(?:ay)?\s*ago', html, re.IGNORECASE))
    
    pattern = rf'{target_days + 1}\s*d(?:ays?)?\s*ago'
    return bool(re.search(pattern, html, re.IGNORECASE))


def extract_news_item(item, symbol: str, target_days: Optional[int], 
                     exact_day_only: bool) -> Optional[Dict]:
    """Extract data from a single news item."""
    try:
        # Skip ads
        if any(cls in item.get('class', []) for cls in ['ad-item', 'native-ad']):
            return None
        
        # Check if item contains symbol
        if symbol not in str(item):
            return None
        
        data = {'tickers': symbol}
        
        # Extract headline
        if headline := item.find('h3', class_=re.compile(r'clamp.*yf-')):
            data['title'] = headline.get_text(strip=True)
        else:
            return None
        
        # Extract URL
        if link := item.find('a', {'data-ylk': re.compile(r'.*hdln.*')}):
            url = link.get('href')
            data['url'] = url if url.startswith('http') else f'https://ca.finance.yahoo.com{url}'
        
        # Extract timestamp and date
        if time_elem := item.find('div', class_=re.compile(r'publishing.*yf-')):
            time_text = time_elem.get_text(strip=True)
            timestamp = time_text.split('•')[-1].strip() if '•' in time_text else time_text
            data['timestamp'] = timestamp
            data['date'] = parse_relative_time(timestamp)
            
            # Filter by date if needed
            if target_days is not None:
                article_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                days_ago = (datetime.now().date() - article_date).days
                
                if exact_day_only and days_ago != target_days:
                    return None
                if not exact_day_only and days_ago > target_days:
                    return None
        
        return data
        
    except Exception as e:
        logger.debug(f"Error extracting news item: {e}")
        return None


def load_page(driver: webdriver.Chrome, url: str, max_retries: int = 3) -> None:
    """Load page with retry logic."""
    for attempt in range(max_retries):
        try:
            driver.get(url)
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "stream-items"))
            )
            logger.info("Page loaded successfully")
            return
        except Exception as e:
            logger.warning(f"Load attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(3)


def scroll_to_target(driver: webdriver.Chrome, target_days: int, max_scrolls: int) -> bool:
    """Scroll until target days content is found."""
    for scroll in tqdm(range(max_scrolls), desc=f"Scrolling to {target_days}d ago"):
        if check_target_reached(driver.page_source, target_days):
            logger.info(f"Target reached after {scroll + 1} scrolls")
            return True
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)  # Reduced from 2s
    
    logger.warning(f"Target not reached after {max_scrolls} scrolls")
    return False


def scrape_yahoo_finance(symbol: str, target_days: int = 1, max_scrolls: int = 10,
                        exact_day_only: bool = False, headless: bool = True) -> List[Dict]:
    """
    Scrape Yahoo Finance news for a symbol.
    
    Args:
        symbol: Stock ticker symbol
        target_days: Number of days back to scrape (0 = today only)
        max_scrolls: Maximum scroll iterations
        exact_day_only: If True, return only news from exactly target_days ago
        headless: Run browser in headless mode
        
    Returns:
        List of news item dictionaries
    """
    url = BASE_URL.format(symbol=symbol)
    driver = None
    
    try:
        logger.info(f"Starting scrape: {symbol} (target_days={target_days})")
        
        driver = create_driver(headless=headless)
        load_page(driver, url)
        scroll_to_target(driver, target_days, max_scrolls)
        
        # Parse content
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        container = soup.find('ul', class_='stream-items yf-9xydx9')
        
        if not container:
            logger.warning("No news container found")
            return []
        
        # Extract news items
        items = container.find_all('li', class_='stream-item')
        news_items = []
        
        for item in tqdm(items, desc="Extracting news", leave=False):
            if news_item := extract_news_item(item, symbol, target_days+1, exact_day_only):
                news_items.append(news_item)
            time.sleep(0.3)  # Reduced rate limiting
        
        logger.info(f"Scraped {len(news_items)} items for {symbol}")
        return news_items
        
    except Exception as e:
        logger.error(f"Scraping error for {symbol}: {e}")