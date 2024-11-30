import asyncio
from typing import Optional
from Wikipedia.wikipedia_api import AsyncWikipediaAPI
from Wikipedia.wikipedia_page import WikipediaPage


class AsyncWikipediaService:
    def __init__(self, api: AsyncWikipediaAPI):
        self.api = api

    async def get_page(self, title: str) -> Optional[WikipediaPage]:
        page_data = await self.api.fetch_page(title)
        if page_data:
            pages = page_data.get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                if page_id != "-1":
                    content = page_info.get("extract", "")
                    links_data = page_info.get("links", [])
                    links = [link.get("title", "") for link in links_data]
                    return WikipediaPage(title=title, content=content, links=links)
        return None

    async def search_page(self, title: str) -> Optional[list[str]]:
        page_data = await self.api.search_page(title)
        if page_data[1]:
            return page_data[1]
        return None

    async def fetch_many_pages(self, links: list[str]) -> list[WikipediaPage | None]:
        tasks = [self.get_page(link) for link in links]
        return await asyncio.gather(*tasks)