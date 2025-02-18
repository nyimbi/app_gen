"""
AsyncWebScraper module

Async version of WebScraper

Classes:

- AsyncWebScraper

"""

from ..core import WebScraper


class AsyncWebScraper(WebScraper):
    """Async version of WebScraper"""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Cleanup resources"""
        if hasattr(self, "session"):
            await self.session.close()

    async def scrape_page_async(self, url: str) -> Optional[ScrapedContent]:
        """Async version of scrape_page"""
        try:
            if not self.should_scrape(url):
                return None
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.config.timeout) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
                    return self.extract_content(html, url, response.status)
        except Exception as e:
            logger.error(f"Async scraping error for {url}: {e}")
            return None
