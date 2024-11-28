import asyncio
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Optional, Dict, Any

import aiohttp
import re


class AsyncWikipediaAPI:
    """Asynchronous Wikipedia API wrapper."""

    BASE_URL = "https://{language}.wikipedia.org/w/api.php"

    def __init__(self, language: str = "en"):
        self.language = language
        self.session = aiohttp.ClientSession()

    def __del__(self):
        try:
            loop = asyncio.get_event_loop()
            asyncio.create_task(self._close_session())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._close_session())

    async def fetch_page(self, title: str) -> Optional[Dict]:
        """
        Fetch Wikipedia page data asynchronously using the API.
        :param title: Title of the Wikipedia page.
        :return: Parsed JSON response or None if the page doesn't exist.
        """
        url = self.BASE_URL.format(language=self.language)
        params = {
            "action": "query",
            "prop": "extracts|links",
            "explaintext": 'True',
            "titles": title,
            "format": "json",
        }

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()

            return None

    async def _close_session(self):
        await self.session.close()

    async def search_page(self, title: str) -> Optional[list[str | list[str]]]:
        """
        Fetch Wikipedia page data asynchronously using the API.
        :param title: Title of the Wikipedia page.
        :return: Parsed JSON response or None if the page doesn't exist.
        """
        url = self.BASE_URL.format(language=self.language)
        params = {
            "action": "opensearch",
            "search": title,
        }

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()

            return None


class WikipediaPage:
    """Represents a Wikipedia page with its content and links."""

    id: int
    title: str
    content: str
    links: list[str]

    def __init__(self, id: int, title: str, content: Optional[str] = None, links: Optional[list[str]] = None):
        """
        Initialize a WikipediaPage instance.
        :param title: Title of the Wikipedia page.
        :param content: Content (extract) of the page.
        :param links: List of page titles linked from this page.
        """
        self.id = id
        self.title = title
        self.content = content or ""
        self.links = links or []

    def word_in_content(self, word: str) -> bool:
        """
        Check if a word exists in the page content (case insensitive).
        :param word: Word to search for.
        :return: True if the word exists, False otherwise.
        """
        return bool(re.search(rf"\b{re.escape(word)}\b", self.content, re.IGNORECASE))


class AsyncWikipediaService:
    """High-level service for interacting with the Wikipedia API."""

    def __init__(self, api: AsyncWikipediaAPI):
        self.api = api

    async def get_page(self, title: str) -> Optional[WikipediaPage]:
        """
        Get a Wikipedia page, including its content and links.
        :param title: Title of the Wikipedia page.
        :return: WikipediaPage object, or None if the page doesn't exist.
        """
        page_data = await self.api.fetch_page(title)
        # print(title)
        if page_data:
            pages = page_data.get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                if page_id != "-1":  # Page exists
                    content = page_info.get("extract", "")
                    links_data = page_info.get("links", [])
                    links = [link.get("title", "") for link in links_data]
                    return WikipediaPage(id=page_id, title=title, content=content, links=links)
        return None

    async def search_page(self, title: str) -> Optional[list[str]]:
        page_data = await self.api.search_page(title)
        if page_data[1]:
            return page_data[1]
        return None

    async def fetch_many_pages(self, links: list[str]) -> list[WikipediaPage | None]:
        """
        Fetch multiple Wikipedia pages asynchronously using the API.
        :param links: List of page titles to fetch.
        :return: List of parsed JSON responses.
        """
        # print(links,32143124123412341)
        tasks = [self.get_page(link) for link in links]
        return await asyncio.gather(*tasks)


class Worker:
    """Worker for processing Wikipedia pages asynchronously."""

    def __init__(self, queue, api: AsyncWikipediaService, visited, succeed_distance, distance_by_page, stop_event, executor, worker_id,
                 target_word):
        self.queue = queue
        self.api = api
        self.visited = visited
        self.distance_by_page = distance_by_page
        self.stop_event = stop_event
        self.executor = executor
        self.worker_id = worker_id
        self.target_word = target_word
        self.succeed_distance = succeed_distance

    async def process(self):
        """Process items in the queue."""
        print(self.worker_id, self.queue)
        timeout_count = 0
        while not self.stop_event.is_set():
            try:
                current_page: WikipediaPage = await asyncio.wait_for(self.queue.get(), timeout=1)
            except asyncio.TimeoutError:
                if timeout_count >= 3:
                    self.queue.task_done()
                    return None
                print(f"Worker {self.worker_id}: Timeout.")
                timeout_count += 1
                continue

            timeout_count = 0

            current_distance = self.distance_by_page[current_page.title]
            if self.succeed_distance['distance'] != 0 and self.succeed_distance['distance'] <= current_distance:
                continue
            # if self.succeed_distance['distance'] != 0 and self.succeed_distance['distance'] >= current_distance:
            #     self.queue.task_done()
            #     return None
            # print(f"Worker {self.worker_id}: Checking page {current_page.title}, Distance: {current_distance}")

            # Check the current page
            # loop = asyncio.get_running_loop()
            pages = await self.api.fetch_many_pages(current_page.links)
            pages = [page for page in pages if page is not None]
            # Add new links to the queue
            for page in pages:
                if page.title not in self.visited:
                    print(self.worker_id, current_distance, page.title, page.word_in_content(self.target_word))
                    if page.word_in_content(self.target_word):
                        # self.stop_event.set()
                        self.queue.task_done()
                        if self.succeed_distance['distance'] != 0 and self.succeed_distance['distance'] > current_distance:
                            self.succeed_distance['distance'] = current_distance
                        else:
                            self.succeed_distance['distance'] = current_distance
                        return current_distance
                    self.visited.add(page.title)
                    await self.queue.put(page)  # nee to send wikipage
                    self.distance_by_page[page.title] = current_distance + 1

            self.queue.task_done()

        print(f"Worker {self.worker_id}: Finished.")
        return None


class WikipediaDistanceFinder:
    """Main class to find the distance between two words via Wikipedia links."""

    api: AsyncWikipediaService

    def __init__(self, wikipedia: AsyncWikipediaService, num_workers=3):
        self.api = wikipedia
        self.num_workers = num_workers

    async def find_distance(self, start_page: WikipediaPage, target_word):
        """Find the minimum distance between two words via Wikipedia links."""
        if start_page.word_in_content(target_word):
            return 1

        queue = asyncio.Queue()
        visited = set()
        distance_by_page = {}
        stop_event = asyncio.Event()

        # Initialize the queue
        visited.add(start_page.title)
        distance_by_page[start_page.title] = 0
        await queue.put(start_page)
        # Create a ProcessPoolExecutor for multiprocessing
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            # Create worker tasks
            succeed_distance = {'distance': 0}
            tasks = [
                asyncio.create_task(
                    Worker(queue, self.api, visited, succeed_distance, distance_by_page, stop_event, executor, worker_id,
                           target_word).process()
                )
                for worker_id in range(self.num_workers)
            ]
            distances = await asyncio.gather(*tasks, return_exceptions=True)

            # Wait for the queue to be processed or the stop_event to be set
            # await queue.join()
            #
            # Cancel remaining workers
            # for task in tasks:
            #     task.cancel()

        # Find the result from workers
        return min(d for d in distances if isinstance(d, int)) if distances else None

    async def calculate_distance(self, word1, word2):
        """Calculate the distance between two words using Wikipedia links."""
        pages = await self.api.search_page(word1)

        if not pages:
            print(f"The pages '{word1}' does not exist.")
            return None

        print('There are several pages which may be referred to by the word:')
        for key, title in enumerate(pages):
            print(f"[{key}] {title}")
        # selected_index = int(input('Write the number of the page you want to use: '))
        selected_index = 1
        page = await self.api.get_page(pages[selected_index])

        distance = await self.find_distance(page, word2)

        if distance:
            print(f"Distance between '{word1}' and '{word2}': {distance}")
        else:
            print("Word not found within the search depth.")


async def main():
    api = AsyncWikipediaAPI()
    service = AsyncWikipediaService(api)
    finder = WikipediaDistanceFinder(service, num_workers=10)
    word1 = "Python"
    word2 = "lviv"
    await finder.calculate_distance(word1, word2)


# Example usage
if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(test())
