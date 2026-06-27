from __future__ import annotations

import time
from dataclasses import dataclass

import requests


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int
    html: str
    error: str = ""


class ArticleFetcher:
    def __init__(self, timeout: int = 20, delay_seconds: float = 1.0, user_agent: str | None = None):
        self.timeout = timeout
        self.delay_seconds = delay_seconds
        self.user_agent = user_agent or "Mozilla/5.0 SEOArticleAnalyzer/4.0"

    def fetch(self, url: str) -> FetchResult:
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,uk;q=0.8,en;q=0.7",
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
            )
            time.sleep(self.delay_seconds)

            return FetchResult(
                url=url,
                final_url=response.url,
                status_code=response.status_code,
                html=response.text or "",
                error="",
            )
        except Exception as error:
            return FetchResult(
                url=url,
                final_url=url,
                status_code=0,
                html="",
                error=str(error),
            )
