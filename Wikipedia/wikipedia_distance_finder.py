import asyncio
from concurrent.futures import ProcessPoolExecutor

from Wikipedia.wikipedia_finder_worker import Worker
from Wikipedia.wikipedia_page import WikipediaPage
from Wikipedia.wikipedia_service import AsyncWikipediaService
from Logger.logger_interface import LoggerInterface


class WikipediaDistanceFinder:
    _wikipedia_service: AsyncWikipediaService
    _logger: LoggerInterface

    def __init__(self, wikipedia: AsyncWikipediaService, logger: LoggerInterface, num_workers=3):
        self._logger = logger
        self._wikipedia_service = wikipedia
        self.num_workers = num_workers

    async def find_distance(self, start_page: WikipediaPage, target_word: str):
        if start_page.word_in_content(target_word):
            return 1

        queue = asyncio.Queue()
        visited = set()
        distance_by_page = {}

        visited.add(start_page.title.lower())
        distance_by_page[start_page.title.lower()] = 1
        await queue.put(start_page)
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            succeed_distance = {'distance': 0}
            tasks = [
                asyncio.create_task(
                    Worker(
                        queue,
                        self._logger,
                        self._wikipedia_service,
                        visited,
                        succeed_distance,
                        distance_by_page,
                        executor,
                        worker_id,
                        target_word
                    ).process()
                )
                for worker_id in range(self.num_workers)
            ]
            distances = await asyncio.gather(*tasks, return_exceptions=True)

        return min(d for d in distances if isinstance(d, int)) if distances else None

