# import wikipediaapi
from typing import Optional
from collections import deque
import asyncio

from aiohttp import ClientSession

from wikipediaApi import AsyncWikipediaAPI

from wikipediaapi import WikipediaPage, Wikipedia
import re

wiki_wiki = Wikipedia('utea te')  # Initialize Wikipedia API globally


def word_in_article(wikiPage: str, word: str) -> bool:
    """Check if the word exists in the article text (case insensitive)."""
    return bool(re.search(rf'\b{re.escape(word)}\b', wikiPage, re.IGNORECASE))


def fetch_article_content(title: str) -> Optional[WikipediaPage]:
    """Fetch the text of a Wikipedia article."""
    page = wiki_wiki.page(title)
    return page if page.exists() else None


async def process_all_links(arr) -> list:
    tasks = []
    for link in arr:
        tasks.append(asyncio.to_thread(link.exists))
    a = await asyncio.gather(*tasks)
    return tasks


async def findDistance(word1: WikipediaPage, word2: str, ):
    if word_in_article(word1.text, word2):
        return 1
    pagesQueue = deque()
    distanceByPage = {}

    pagesQueue.append(word1)

    distanceByPage[str(word1)] = 1

    async with ClientSession() as session:
        while pagesQueue:
            current_page = pagesQueue.popleft()
            print(distanceByPage[str(current_page)], current_page)

            # Gather links asynchronously
            tasks = await process_all_links(current_page.links.values())
            for page in current_page.links.values():
                if word_in_article(page.text, word2):
                    return distanceByPage[str(current_page)] + 1
                print(str(page))
                pagesQueue.append(page)
                distanceByPage[str(page)] = distanceByPage[str(current_page)] + 1

    return None


async def calculate_distance(word1, word2):
    page = fetch_article_content(word1)

    if 'may refer to:' in page.summary:
        print('here are severel page which may be reffered to by the word')
        print('please choose the one you want to use:')
        links = list(page.links.values())

        for key, link in enumerate(links):
            print(f"[{key}] {link.title}")
        page = links[int(input('write the number of the page you want to use: '))]
        page.exists()

    distance = await findDistance(page, word2)

    if distance:
        print(f"Distance between '{word1}' and '{word2}': {distance}")

    else:
        return "Word not found within the search depth."


# Example usage
if __name__ == "__main__":
    word1 = "Python"
    word2 = "chervonograd"
    asyncio.run(calculate_distance(word1, word2))
