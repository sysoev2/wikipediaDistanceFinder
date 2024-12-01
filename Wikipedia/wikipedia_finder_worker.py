import asyncio
from asyncio import Queue
from concurrent.futures import ProcessPoolExecutor
from typing import Set, Dict, Optional, final

from Logger.logger_interface import LoggerInterface
from Wikipedia.wikipedia_page import WikipediaPage
from Wikipedia.wikipedia_service import AsyncWikipediaService


@final
class Worker:
    TIMEOUT = 1
    MAX_TIMEOUTS = 5
    NO_DISTANCE = 0

    def __init__(
        self,
        queue: Queue,
        logger: LoggerInterface,
        api: AsyncWikipediaService,
        visited: Set[str],
        succeed_distance: Dict[str, int],
        distance_by_page: Dict[str, int],
        executor: ProcessPoolExecutor,
        worker_id: int,
        target_word: str,
    ):
        self.__queue = queue
        self.__logger = logger
        self.__api = api
        self.__visited = visited
        self.__distance_by_page = distance_by_page
        self.__executor = executor
        self.__worker_id = worker_id
        self.__target_word = target_word
        self.__succeed_distance = succeed_distance

    async def process(self) -> Optional[int]:
        self.__logger.info(f"Worker {self.__worker_id} started processing.")
        timeout_count = 0

        while True:
            page = await self.__get_next_page(timeout_count)
            if page is None:
                return None

            timeout_count = 0
            if await self.__process_page(page):
                return self.__succeed_distance["distance"]

    async def __get_next_page(self, timeout_count: int) -> Optional[WikipediaPage]:
        try:
            return await asyncio.wait_for(self.__queue.get(), timeout=self.TIMEOUT)
        except asyncio.TimeoutError:
            if timeout_count >= self.MAX_TIMEOUTS:
                self.__logger.info(f"Worker {self.__worker_id}: Max timeouts reached. Exiting.")
                self.__queue.task_done()
                return None
            self.__logger.warning(f"Worker {self.__worker_id}: Timeout {timeout_count + 1}.")
            return None

    async def __process_page(self, current_page: WikipediaPage) -> bool:
        current_distance = self.__distance_by_page[current_page.title.lower()]

        if self.__should_skip_distance(current_distance):
            return False

        for linked_page_title in current_page.links:
            if await self.__process_linked_page(linked_page_title, current_distance):
                return True
        return False

    def __should_skip_distance(self, current_distance: int) -> bool:
        succeed_distance = self.__succeed_distance["distance"]
        return succeed_distance != self.NO_DISTANCE and succeed_distance <= current_distance

    async def __process_linked_page(self, page_title: str, current_distance: int) -> bool:
        distance = current_distance + 1

        if self.__should_skip_distance(distance) or page_title.lower() in self.__visited:
            return False

        page = await self.__api.get_page(page_title)
        if not page:
            return False

        if page.word_in_content(self.__target_word):
            self.__update_succeed_distance(distance)
            self.__logger.info(
                f"Worker {self.__worker_id}: Found target word in {page.title} at distance {distance}."
            )
            return True

        self.__visited.add(page.title.lower())
        await self.__queue.put(page)
        self.__distance_by_page[page.title.lower()] = distance
        return False

    def __update_succeed_distance(self, distance: int):
        succeed_distance = self.__succeed_distance["distance"]
        if succeed_distance == self.NO_DISTANCE or distance < succeed_distance:
            self.__succeed_distance["distance"] = distance
