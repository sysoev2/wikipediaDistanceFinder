from typing import Optional
import re


class WikipediaPage:
    title: str
    content: str
    links: list[str]

    def __init__(self, title: str, content: Optional[str] = None, links: Optional[list[str]] = None):
        self.title = title
        self.content = content or ""
        self.links = links or []

    def word_in_content(self, word: str) -> bool:
        return bool(re.search(rf"\b{re.escape(word)}\b", self.content, re.IGNORECASE))
