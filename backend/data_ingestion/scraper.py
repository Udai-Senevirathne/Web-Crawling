"""
Web scraper to extract content from target website.
Supports Playwright for JavaScript-rendered pages and falls back to requests for simpler pages.
"""
import asyncio
import sys
import logging
from bs4 import BeautifulSoup
import aiohttp
from typing import List, Dict, Set
import os
from urllib.parse import urljoin, urlparse
import requests

logger = logging.getLogger(__name__)


class WebScraper:
    def __init__(self, base_url: str, max_pages: int = 100, max_depth: int = 3):
        self.base_url = base_url.rstrip('/')
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited_urls: Set[str] = set()
        self.domain = urlparse(base_url).netloc
        self.use_playwright = os.getenv('USE_PLAYWRIGHT', 'false').lower() == 'true'

    async def crawl(self) -> List[Dict]:
        """Crawl website and extract pages."""
        if self.use_playwright:
            return await self._crawl_with_playwright()
        else:
            return await self._crawl_with_requests()

    async def _crawl_with_playwright(self) -> List[Dict]:
        """Crawl using Playwright for JavaScript-rendered pages."""
        pages = []

        try:
            # Set Windows event loop policy for subprocess support
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # Start crawling from base URL
                await self._crawl_page_playwright(page, self.base_url, pages, depth=0)

                await browser.close()
        except Exception as e:
            logger.warning("Playwright crawling failed: %s", e)
            logger.info("Falling back to requests-based crawling...")
            return await self._crawl_with_requests()

        return pages

    async def _crawl_with_requests(self) -> List[Dict]:
        """Crawl using requests/aiohttp (simpler, works on all platforms)."""
        pages = []
        self.visited_urls.clear()
        
        await self._crawl_page_requests(self.base_url, pages, depth=0)
        
        return pages

    async def _crawl_page_requests(self, url: str, pages: List, depth: int):
        """Crawl a page using requests (sync but wrapped in async)."""
        if url in self.visited_urls or len(pages) >= self.max_pages or depth > self.max_depth:
            return

        self.visited_urls.add(url)

        try:
            logger.info("Crawling: %s (depth: %d)", url, depth)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')

            page_data = {
                'url': url,
                'title': self._extract_title(soup, url),
                'content': self._extract_text(soup),
                'links': self._extract_links(soup, url)
            }

            pages.append(page_data)
            title_preview = (page_data['title'] or 'No title')[:50]
            logger.info("[OK] Extracted: %s...", title_preview)

            # Crawl linked pages
            for link in page_data['links'][:10]:
                if self._should_crawl(link):
                    await self._crawl_page_requests(link, pages, depth + 1)
                    # Small delay to be polite
                    await asyncio.sleep(0.5)

        except Exception as e:
            logger.warning("Error crawling %s: %s", url, e)

    async def _crawl_page_playwright(self, page, url: str, pages: List, depth: int):
        """Recursively crawl pages using Playwright."""
        if url in self.visited_urls or len(pages) >= self.max_pages or depth > self.max_depth:
            return

        self.visited_urls.add(url)

        try:
            logger.info("Crawling: %s (depth: %d)", url, depth)
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Wait a bit for dynamic content
            await asyncio.sleep(1)

            content = await page.content()

            # Extract content
            soup = BeautifulSoup(content, 'html.parser')

            page_data = {
                'url': url,
                'title': self._extract_title(soup, url),
                'content': self._extract_text(soup),
                'links': self._extract_links(soup, url)
            }

            pages.append(page_data)
            logger.info("[OK] Extracted: %s...", page_data['title'][:50])

            # Crawl linked pages (limited per page)
            for link in page_data['links'][:10]:
                if self._should_crawl(link):
                    await self._crawl_page_playwright(page, link, pages, depth + 1)

        except Exception as e:
            logger.warning("Error crawling %s: %s", url, e)

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract a descriptive title for the page."""
        # Try to get h1 first (usually more descriptive)
        h1 = soup.find('h1')
        if h1 and h1.get_text(strip=True):
            title = h1.get_text(strip=True)[:100]
            if len(title) > 10:  # Reasonable length for a title
                return title
        
        # Fall back to title tag
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            # Remove common suffixes like "| SLTMobitel" or " - Company Name"
            for separator in [' | ', ' - ', ' – ', ' — ']:
                if separator in title:
                    parts = title.split(separator)
                    # Take the first part if it's meaningful
                    if len(parts[0]) > 5:
                        title = parts[0].strip()
                        break
            if title:
                return title[:100]
        
        # Extract from URL path as last resort
        parsed = urlparse(url)
        path = parsed.path.strip('/').replace('-', ' ').replace('_', ' ')
        if path:
            # Capitalize words
            title = ' '.join(word.capitalize() for word in path.split('/')[-1].split())
            return title[:100] if title else 'Web Page'
        
        return 'Web Page'

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content."""
        # Remove script, style, nav, and footer elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
            element.decompose()

        # Get text
        text = soup.get_text(separator='\n')

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        text = '\n'.join(line for line in lines if line)

        return text

    def _extract_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extract and normalize links."""
        links = []

        for a in soup.find_all('a', href=True):
            href = a['href']

            # Convert relative to absolute URLs
            absolute_url = urljoin(current_url, href)

            # Only include links from same domain
            if urlparse(absolute_url).netloc == self.domain:
                # Remove fragments and query parameters for consistency
                clean_url = absolute_url.split('#')[0].split('?')[0]
                if clean_url not in links:
                    links.append(clean_url)

        return links

    def _should_crawl(self, url: str) -> bool:
        """Determine if URL should be crawled."""
        # Exclude common non-content URLs
        exclude_patterns = [
            '/login', '/register', '/signup', '/signin',
            '/admin', '/api/', '/auth/',
            '.pdf', '.jpg', '.png', '.gif', '.svg',
            '.zip', '.doc', '.docx', '.xls', '.xlsx',
            '/download', '/uploads',
            'javascript:', 'mailto:', 'tel:'
        ]

        url_lower = url.lower()
        return not any(pattern in url_lower for pattern in exclude_patterns)


# CLI usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Scrape website content')
    parser.add_argument('--url', required=True, help='Website URL to crawl')
    parser.add_argument('--max-pages', type=int, default=50, help='Maximum pages to crawl')
    parser.add_argument('--max-depth', type=int, default=3, help='Maximum crawl depth')
    parser.add_argument('--playwright', action='store_true', help='Use Playwright for JS-rendered pages')
    args = parser.parse_args()

    if args.playwright:
        os.environ['USE_PLAYWRIGHT'] = 'true'

    scraper = WebScraper(args.url, max_pages=args.max_pages, max_depth=args.max_depth)
    pages = asyncio.run(scraper.crawl())

    print(f"\n{'='*60}")
    print(f"[OK] Crawling complete!")
    print(f"[OK] Total pages scraped: {len(pages)}")
    print(f"{'='*60}")
