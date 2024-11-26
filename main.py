import asyncio
import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor
from wikipediaapi import WikipediaPage, Wikipedia
import re

wiki_wiki = Wikipedia('entes tewat')  # Initialize Wikipedia API globally


def word_in_article(text: str, word: str) -> bool:
    """Check if the word exists in the article text (case insensitive)."""
    return bool(re.search(rf'\b{re.escape(word)}\b', text, re.IGNORECASE))


def fetch_article_content(title: str):
    """Fetch the text of a Wikipedia article."""
    page = wiki_wiki.page(title)
    return page if page.exists() else None


def process_page_sync(page: WikipediaPage, word: str) -> bool:
    """Synchronous function to check if a word exists in the page."""
    return word_in_article(page.text, word)


async def worker(queue, visited, distance_by_page, stop_event, executor, worker_id):
    """Worker to process items in the queue."""
    while not stop_event.is_set():
        try:
            current_page = await asyncio.wait_for(queue.get(), timeout=1)
        except asyncio.TimeoutError:

            continue

        current_distance = distance_by_page[str(current_page)]
        print(f"Worker {worker_id}: Checking page {str(current_page)}, Distance: {current_distance}")

        # Check the current page
        loop = asyncio.get_running_loop()
        found = await loop.run_in_executor(executor, process_page_sync, current_page, word2)

        if found:
            stop_event.set()
            print(f"Worker {worker_id}: Found target word in {str(current_page)}")
            queue.task_done()
            return current_distance + 1

        # Add new links to the queue
        for page in current_page.links.values():
            if str(page) not in visited:
                visited.add(str(page))
                await queue.put(page)
                distance_by_page[str(page)] = current_distance + 1

        queue.task_done()

    print(f"Worker {worker_id}: Finished.")
    return None


async def find_distance(start_page, word2: str, num_workers=10):
    """Find the minimum distance between two words via Wikipedia links."""
    if word_in_article(start_page.text, word2):
        return 1

    queue = asyncio.Queue()
    visited = set()
    distance_by_page = {}
    stop_event = asyncio.Event()

    # Initialize the queue
    visited.add(str(start_page))
    distance_by_page[str(start_page)] = 0
    await queue.put(start_page)

    # Create a ProcessPoolExecutor for multiprocessing
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Create worker tasks
        tasks = [
            asyncio.create_task(worker(queue, visited, distance_by_page, stop_event, executor, worker_id))
            for worker_id in range(num_workers)
        ]

        # Wait for the queue to be processed or the stop_event to be set
        await stop_event.wait()

        # Cancel remaining workers
        for task in tasks:
            task.cancel()
        distances = await asyncio.gather(*tasks, return_exceptions=True)

    # Find the result from workers
    return min(d for d in distances if isinstance(d, int)) if distances else None


async def calculate_distance(word1, word2):
    """Calculate the distance between two words using Wikipedia links."""
    page = fetch_article_content(word1)

    if not page or not page.exists():
        print(f"The page '{word1}' does not exist.")
        return None

    if 'may refer to:' in page.summary:
        print('There are several pages which may be referred to by the word:')
        links = list(page.links.values())
        for key, link in enumerate(links):
            print(f"[{key}] {link.title}")
        selected_index = int(input('Write the number of the page you want to use: '))
        page = links[selected_index]

    distance = await find_distance(page, word2)

    if distance:
        print(f"Distance between '{word1}' and '{word2}': {distance}")
    else:
        print("Word not found within the search depth.")


# Example usage
if __name__ == "__main__":
    start = time.time()

    word1 = "Python"
    word2 = "lviv"
    asyncio.run(calculate_distance(word1, word2))
    end = time.time()
    print('Script took',end - start, 'sec to processed')
