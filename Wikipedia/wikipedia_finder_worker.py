import asyncio
from asyncio import Queue
from concurrent.futures import ProcessPoolExecutor
from typing import final

from Logger.logger_interface import LoggerInterface
from Wikipedia.wikipedia_page import WikipediaPage
from Wikipedia.wikipedia_service import AsyncWikipediaService


@final
class Worker:
    __queue: Queue
    __logger: LoggerInterface
    __api: AsyncWikipediaService
    __visited: set
    __succeed_distance: dict
    __distance_by_page: dict
    __executor: ProcessPoolExecutor
    __worker_id: int
    __target_word: str

    def __init__(
            self,
            queue: Queue,
            logger: LoggerInterface,
            api: AsyncWikipediaService,
            visited: set,
            succeed_distance: dict,
            distance_by_page: dict,
            executor: ProcessPoolExecutor,
            worker_id: int,
            target_word: str
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

    async def process(self):
        self.__logger.info(f"process Worker:{self.__worker_id}")
        timeout_count = 0
        while True:
            try:
                current_page: WikipediaPage = await asyncio.wait_for(self.__queue.get(), timeout=1)
            except:
                if timeout_count >= 5:
                    self.__logger.info(f"Worker {self.__worker_id}: failed.")
                    self.__queue.task_done()
                    return None
                self.__logger.info(f"Worker {self.__worker_id}: Timeout.")
                timeout_count += 1
                continue

            timeout_count = 0

            current_distance = self.__distance_by_page[current_page.title.lower()]
            if self.__succeed_distance['distance'] != 0 and self.__succeed_distance['distance'] <= current_distance:
                continue
            distance = current_distance + 1
            for page in current_page.links:
                self.__logger.debug(f"Worker {self.__worker_id}: {page} - {distance}")
                if self.__succeed_distance['distance'] != 0 and self.__succeed_distance['distance'] <= distance:
                    continue
                if page.lower() not in self.__visited:
                    page = await self.__api.get_page(page)
                    if page is None:
                        continue
                    if page.word_in_content(self.__target_word):
                        self.__logger.info(f"Worker {self.__worker_id}: Found target word. {page.title} - {distance}")
                        if (
                                self.__succeed_distance['distance'] != 0
                                and self.__succeed_distance['distance'] > distance
                        ):
                            self.__succeed_distance['distance'] = distance
                        elif self.__succeed_distance['distance'] == 0:
                            self.__succeed_distance['distance'] = distance
                        return distance
                    self.__visited.add(page.title.lower())
                    await self.__queue.put(page)
                    self.__distance_by_page[page.title.lower()] = distance
        return None