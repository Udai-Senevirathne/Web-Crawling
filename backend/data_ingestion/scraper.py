"""
Web scraper to extract content from target website.
"""
import asyncio
from bs4 import BeautifulSoup
import aiohttp
from typing import List, Dict, Set
from playwright.async_api import async_playwright
import os
from urllib.parse import urljoin, urlparse


class WebScraper:
    def __init__(self, base_url: str, max_pages: int = 100, max_depth: int = 3):
        self.base_url = base_url.rstrip('/')
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited_urls: Set[str] = set()
        self.domain = urlparse(base_url).netloc

    async def crawl(self) -> List[Dict]:
        """Crawl website and extract pages."""
        pages = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # Start crawling from base URL
                await self._crawl_page(page, self.base_url, pages, depth=0)

                await browser.close()
        except Exception as e:
            print(f"Error during crawling: {e}")

        return pages

    async def _crawl_page(self, page, url: str, pages: List, depth: int):
        """Recursively crawl pages."""
        if url in self.visited_urls or len(pages) >= self.max_pages or depth > self.max_depth:
            return

        self.visited_urls.add(url)

        try:
            print(f"Crawling: {url} (depth: {depth})")
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Wait a bit for dynamic content
            await asyncio.sleep(1)

            content = await page.content()

            # Extract content
            soup = BeautifulSoup(content, 'html.parser')

            page_data = {
                'url': url,
                'title': soup.title.string if soup.title else '',
                'content': self._extract_text(soup),
                'links': self._extract_links(soup, url)
            }

            pages.append(page_data)
            print(f"[OK] Extracted: {page_data['title'][:50]}...")

            # Crawl linked pages (limited per page)
            for link in page_data['links'][:10]:
                if self._should_crawl(link):
                    await self._crawl_page(page, link, pages, depth + 1)

        except Exception as e:
            print(f"Error crawling {url}: {e}")

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content."""
        # Remove script, style, nav, and footer elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
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
    args = parser.parse_args()

    scraper = WebScraper(args.url, max_pages=args.max_pages, max_depth=args.max_depth)
    pages = asyncio.run(scraper.crawl())

    print(f"\n{'='*60}")
    print(f"[OK] Crawling complete!")
    print(f"[OK] Total pages scraped: {len(pages)}")
    print(f"{'='*60}")

