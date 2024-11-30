import asyncio
from Wikipedia.wikipedia_api import AsyncWikipediaAPI
from Wikipedia.wikipedia_distance_finder import WikipediaDistanceFinder
from Wikipedia.wikipedia_service import AsyncWikipediaService
from input_processor import InputProcessor
import os
from dotenv import load_dotenv
from Logger.logger_factory import LoggerFactory
from Logger.dummy_logger import DummyLogger

def get_bool_env_variable(name: str, default_value: bool | None = None) -> bool:
    true_ = ('true', '1', 't')
    false_ = ('false', '0', 'f')
    value: str | None = os.getenv(name, None)
    if value is None:
        if default_value is None:
            raise ValueError(f'Variable `{name}` not set!')
        else:
            value = str(default_value)
    if value.lower() not in true_ + false_:
        raise ValueError(f'Invalid value `{value}` for variable `{name}`')
    return value in true_


async def main():
    if not bool(get_bool_env_variable('APP_DEBUG', False)):
        logger = DummyLogger()
    else:
        logger = LoggerFactory.get_logger(os.getenv("DEBUG_TYPE", "console"))
    api = AsyncWikipediaAPI(logger)
    service = AsyncWikipediaService(api)
    finder = WikipediaDistanceFinder(service, logger, int(os.getenv("NUM_WORKERS", 10)))
    word1 = InputProcessor.get_wiki_page()
    pages = await service.search_page(word1)
    selected_index = InputProcessor.get_valid_index(pages)
    page = await service.get_page(pages[selected_index])
    word2 = InputProcessor.get_word()



    if not pages:
        print(f"The pages '{word1}' does not exist.")
        return None

    print('counting please wait...')

    distance = await finder.find_distance(page, word2)

    if distance is not None:
        print(f"The distance between '{word1}' and '{word2}' is {distance}.")
    else:
        print(f"The distance between '{word1}' and '{word2}' could not be calculated.")



if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
