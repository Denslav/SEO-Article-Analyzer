from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

try:
    import trafilatura
except Exception:
    trafilatura = None


@dataclass
class ParsedArticle:
    url: str
    final_url: str
    status_code: int
    title: str = ""
    meta_description: str = ""
    canonical: str = ""
    h1: str = ""
    h2: list[str] = field(default_factory=list)
    h3: list[str] = field(default_factory=list)
    text: str = ""
    word_count: int = 0
    questions: list[str] = field(default_factory=list)
    error: str = ""


class ArticleParser:
    def parse(self, url: str, final_url: str, status_code: int, html: str, error: str = "") -> ParsedArticle:
        if error:
            return ParsedArticle(url=url, final_url=final_url, status_code=status_code, error=error)

        soup = BeautifulSoup(html or "", "lxml")

        title = self._get_title(soup)
        meta_description = self._get_meta_description(soup)
        canonical = self._get_canonical(soup)
        h1 = self._first_heading(soup, "h1")
        h2 = self._headings(soup, "h2")
        h3 = self._headings(soup, "h3")
        text = self._extract_main_text(html=html, soup=soup)
        questions = self._extract_questions(text=text, headings=[h1, *h2, *h3])
        word_count = self._count_words(text)

        return ParsedArticle(
            url=url,
            final_url=final_url,
            status_code=status_code,
            title=title,
            meta_description=meta_description,
            canonical=canonical,
            h1=h1,
            h2=h2,
            h3=h3,
            text=text,
            word_count=word_count,
            questions=questions,
            error="",
        )

    def _get_title(self, soup: BeautifulSoup) -> str:
        if soup.title and soup.title.string:
            return self._clean_text(soup.title.string)

        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return self._clean_text(og_title["content"])

        return ""

    def _get_meta_description(self, soup: BeautifulSoup) -> str:
        candidates = []

        for attrs in (
            {"name": "description"},
            {"property": "og:description"},
            {"name": "twitter:description"},
        ):
            tag = soup.find("meta", attrs=attrs)
            if tag and tag.get("content"):
                candidates.append(self._clean_text(tag["content"]))

        for candidate in candidates:
            if self._looks_like_good_description(candidate):
                return candidate

        return ""

    def _looks_like_good_description(self, text: str) -> bool:
        lower = text.lower().strip()
        if len(lower) < 40 or len(lower) > 350:
            return False

        bad_fragments = (
            "при содействии", "ed burns", "nicole", "cookie", "cookies",
            "privacy policy", "terms of use", "javascript", "subscribe",
            "подписаться", "комментарии", "читать далее", "перейти к",
            "редактировать", "править код", "материал из википедии",
        )
        return not any(fragment in lower for fragment in bad_fragments)

    def _get_canonical(self, soup: BeautifulSoup) -> str:
        tag = soup.find("link", rel=lambda value: value and "canonical" in value)
        if tag and tag.get("href"):
            return tag["href"].strip()
        return ""

    def _first_heading(self, soup: BeautifulSoup, name: str) -> str:
        tag = soup.find(name)
        return self._clean_text(tag.get_text(" ", strip=True)) if tag else ""

    def _headings(self, soup: BeautifulSoup, name: str) -> list[str]:
        headings = []
        for tag in soup.find_all(name):
            text = self._clean_text(tag.get_text(" ", strip=True))
            if text and self._looks_like_content_heading(text):
                headings.append(text)
        return headings

    def _looks_like_content_heading(self, heading: str) -> bool:
        lower = heading.lower()
        bad = (
            "навигация", "личные инструменты", "пространства имен", "просмотры",
            "перейти к навигации", "содержание", "править код", "см. также",
            "примечания", "литература", "ссылки", "references", "external links",
            "privacy", "cookies", "поделиться", "комментарии",
        )
        return not any(item in lower for item in bad)

    def _extract_main_text(self, html: str, soup: BeautifulSoup) -> str:
        if trafilatura:
            extracted = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_formatting=False,
                favor_precision=True,
            )
            if extracted:
                return self._clean_text(extracted)

        for tag in soup(["script", "style", "noscript", "svg", "form", "nav", "footer", "header", "aside"]):
            tag.decompose()

        candidate = soup.find("article") or soup.find("main") or soup.body or soup
        paragraphs = [p.get_text(" ", strip=True) for p in candidate.find_all(["p", "li"])]
        text = " ".join(paragraphs)
        return self._clean_text(text)

    def _extract_questions(self, text: str, headings: list[str]) -> list[str]:
        candidates = []

        for item in headings:
            item = self._clean_text(item)
            if item and self._looks_like_question(item):
                candidates.append(item)

        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sentence in sentences:
            sentence = self._clean_text(sentence)
            if self._looks_like_question(sentence):
                candidates.append(sentence)

        return list(dict.fromkeys(candidates))

    def _looks_like_question(self, text: str) -> bool:
        if not text:
            return False

        if len(text) < 8 or len(text) > 150:
            return False

        lower = text.lower().strip()

        bad = (
            "what will happen if i do this",
            "can you explain to me why i get sick",
            "what causes what",
            "божиим", "творением", "насколько это обосновано",
            "—", "»", "«", "doi", "isbn", "архивировано",
        )
        if any(item in lower for item in bad):
            return False

        starters = (
            "что ", "как ", "когда ", "где ", "почему ", "зачем ", "какой ", "какая ", "какие ",
            "сколько ", "можно ли ", "чем ", "кто ", "что такое ", "как работает ",
            "що ", "як ", "коли ", "де ", "чому ", "який ", "яка ", "які ",
            "what ", "how ", "when ", "where ", "why ", "which ", "can ", "is ", "are ",
        )

        return "?" in lower and lower.startswith(starters) or lower.startswith(starters)

    def _count_words(self, text: str) -> int:
        return len(re.findall(r"[A-Za-zА-Яа-яЁёІіЇїЄєҐґ0-9]+", text or ""))

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text or "")
        return text.strip()
