from __future__ import annotations

from seo_article_analyzer.core.fetcher import ArticleFetcher
from seo_article_analyzer.core.parser import ArticleParser, ParsedArticle


class ArticleAnalyzer:
    def __init__(self, config: dict):
        fetch_config = config.get("fetch", {})
        self.fetcher = ArticleFetcher(
            timeout=fetch_config.get("timeout", 20),
            delay_seconds=fetch_config.get("delay_seconds", 1),
            user_agent=fetch_config.get("user_agent"),
        )
        self.parser = ArticleParser()

    def analyze_urls(self, query: str, urls: list[str]) -> list[ParsedArticle]:
        articles = []

        for index, url in enumerate(urls, start=1):
            print(f"[{index}/{len(urls)}] Загружаю: {url}")
            result = self.fetcher.fetch(url)
            article = self.parser.parse(
                url=result.url,
                final_url=result.final_url,
                status_code=result.status_code,
                html=result.html,
                error=result.error,
            )
            articles.append(article)

        return articles
