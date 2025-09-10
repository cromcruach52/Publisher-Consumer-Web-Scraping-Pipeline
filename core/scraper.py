import requests
import time
from bs4 import BeautifulSoup
from typing import Optional
from datetime import datetime
from config.settings import ScrapingConfig
from models.article import ScrapedContent
from utils.logger import logger

class Scraper:
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape(self, url: str) -> Optional[ScrapedContent]:
        """Scrape title and content from a URL"""
        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"Scraping {url} (attempt {attempt + 1})")
                
                response = self._fetch_with_timeout(url)
                if not response:
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                title = self._extract_title(soup, url)
                content = self._extract_content(soup)
                
                if title and content:
                    scraped_content = ScrapedContent(
                        title=title,
                        content=content,
                        scraped_at=datetime.utcnow()
                    )
                    logger.info(f"Successfully scraped {url}")
                    return scraped_content
                else:
                    logger.warning(f"Could not extract title or content from {url}")
                
            except Exception as e:
                logger.error(f"Scraping attempt {attempt + 1} failed for {url}: {e}")
                
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.delay_between_requests * (attempt + 1))
        
        logger.error(f"All scraping attempts failed for {url}")
        return None
    
    def _fetch_with_timeout(self, url: str) -> Optional[requests.Response]:
        """Fetch URL with timeout and error handling"""
        try:
            response = self.session.get(
                url, 
                timeout=self.config.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract title using multiple strategies"""
        # Strategy 1: <title> tag
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            title = title_tag.string.strip()
            if title:
                return title
        
        # Strategy 2: h1 tag
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.get_text():
            title = h1_tag.get_text().strip()
            if title:
                return title
        
        # Strategy 3: og:title meta tag
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title = og_title['content'].strip()
            if title:
                return title
        
        logger.warning(f"Could not extract title from {url}")
        return "No Title Found"
    
    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main content using multiple strategies"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Strategy 1: Look for common article containers
        content_selectors = [
            'article',
            '[class*="content"]',
            '[class*="article"]',
            '[class*="post"]',
            'main',
            '.entry-content',
            '#content'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                content = elements[0].get_text(strip=True)
                if len(content) > 100:  # Minimum content length
                    return content[:2000]  # Limit content length
        
        # Strategy 2: Get all paragraph text
        paragraphs = soup.find_all('p')
        if paragraphs:
            content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            if len(content) > 100:
                return content[:2000]
        
        # Strategy 3: Get body text as fallback
        body = soup.find('body')
        if body:
            content = body.get_text(strip=True)
            if len(content) > 100:
                return content[:2000]
        
        logger.warning("Could not extract meaningful content")
        return "No content found"
