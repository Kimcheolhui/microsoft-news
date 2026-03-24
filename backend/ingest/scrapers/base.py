from abc import ABC, abstractmethod

import requests

from ..utils.http import create_session


class BaseScraper(ABC):
    """Abstract base for all source scrapers."""

    def __init__(self) -> None:
        self._http: requests.Session = create_session()

    @abstractmethod
    def scrape(self) -> list[dict]:
        """Fetch and parse updates from the source. Returns list of dicts ready for Update model."""
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Identifier matching sources.name in DB."""
        ...
