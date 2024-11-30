import asyncio
from typing import Optional, Dict
from aiohttp import ClientSession
import aiohttp
from Logger.logger_interface import LoggerInterface


class AsyncWikipediaAPI:
    BASE_URL = "https://en.wikipedia.org/w/api.php"
    __session: ClientSession
    __logger: LoggerInterface

    def __init__(self, logger: LoggerInterface):
        self._logger = logger
        self.__session = aiohttp.ClientSession()

    def __del__(self):
        try:
            loop = asyncio.get_event_loop()
            asyncio.create_task(self._close_session())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._close_session())

    async def fetch_page(self, title: str) -> Optional[Dict]:
        url = self.BASE_URL
        params = {
            "action": "query",
            "prop": "extracts|links",
            "explaintext": 'True',
            "titles": title,
            "format": "json",
            "pllimit": 500
        }

        async with self.__session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 429:
                self._logger.warning(f"Too many requests. Waiting for 2 second. {title}")
                await asyncio.sleep(2)
                return await self.fetch_page(title)

            return None

    async def _close_session(self):
        await self.__session.close()

    async def search_page(self, title: str) -> Optional[list[str | list[str]]]:
        url = self.BASE_URL
        params = {
            "action": "opensearch",
            "search": title,
        }

        async with self.__session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()

            return None


