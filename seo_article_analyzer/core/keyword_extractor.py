from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from seo_article_analyzer.core.lemmatizer import Lemmatizer
from seo_article_analyzer.core.parser import ParsedArticle


QUESTION_WORDS = {
    "что", "как", "где", "когда", "почему", "зачем", "какой", "какая", "какие",
    "чем", "сколько", "можно", "ли", "що", "як", "де", "коли", "чому",
    "what", "how", "where", "when", "why", "which", "can", "is", "are",
}

STOPWORDS = {
    "и", "в", "во", "на", "но", "а", "или", "для", "это", "по", "из", "за", "от", "до",
    "при", "про", "об", "о", "у", "с", "со", "к", "ко", "не", "же", "бы", "мы", "вы",
    "они", "он", "она", "оно", "его", "ее", "их", "так", "также", "если", "то", "есть",
    "может", "будет", "будут", "был", "была", "были", "без", "под", "над", "чтобы",
    "который", "которая", "которые", "более", "менее", "самый", "самая", "уже",
    "і", "та", "це", "з", "із", "від", "є", "може", "буде", "будуть", "був", "була",
    "були", "щоб", "який", "яка", "які", "також",
    "and", "or", "the", "a", "an", "to", "of", "for", "in", "on", "with", "without",
    "from", "by", "this", "that", "these", "those", "as", "at", "it", "its", "you",
    "your", "we", "our", "they", "their",
}

BAD_START = {
    "такое", "такой", "такая", "такие", "таких", "таким", "такими",
    "как", "таких", "которые", "которая", "который", "что", "ли",
    "представляет", "является", "может", "могут", "они", "она", "оно",
    "области", "область", "некоторые", "другие", "например",
    "such", "these", "those", "they", "which", "that",
}

BAD_END = {
    "как", "что", "который", "которая", "которые", "которая", "ии",
    "это", "таких", "таким", "такие", "они", "она", "оно",
    "and", "or", "the", "of", "to", "for", "with", "which", "that",
}

BAD_EXACT = {
    "таких как", "как они", "ии как", "что представляет", "представляет собой",
    "области искусственного", "обработку естественного", "обработка естественного",
    "естественного языка", "искусственный интеллект как", "интеллекта которая",
    "такое искусственный", "такое искусственный интеллект", "интеллект ии",
    "дата обращения", "править код", "перейти навигации", "перейти поиску",
}

BAD_FRAGMENTS = {
    "cookie", "cookies", "privacy", "terms of use", "дата обращения", "архивировано",
    "править код", "перейти к навигации", "перейти к поиску", "материал из википедии",
    "страница последний раз", "см также", "isbn", "doi", "pmid", "архивная копия",
    "read more", "subscribe", "newsletter",
}

ENTITY_PATTERNS = {
    "бухгалтерские услуги": "бухгалтерские услуги",
    "услуги бухгалтера": "услуги бухгалтера",
    "бухгалтерское сопровождение": "бухгалтерское сопровождение",
    "бухгалтерское обслуживание": "бухгалтерское обслуживание",
    "ведение бухгалтерии": "ведение бухгалтерии",
    "бухгалтерский аутсорсинг": "бухгалтерский аутсорсинг",
    "бухгалтер для фоп": "бухгалтер для ФОП",
    "налоговая отчетность": "налоговая отчетность",
    "кадровый учет": "кадровый учет",
    "обработка естественного языка": "обработка естественного языка",
    "машинное обучение": "машинное обучение",
    "глубокое обучение": "глубокое обучение",
    "нейронные сети": "нейронные сети",
    "генеративный искусственный интеллект": "генеративный искусственный интеллект",
    "искусственный интеллект": "искусственный интеллект",
    "computer vision": "computer vision",
    "machine learning": "machine learning",
    "deep learning": "deep learning",
    "neural networks": "neural networks",
    "natural language processing": "natural language processing",
    "artificial intelligence": "artificial intelligence",
}

ENTITY_VARIANTS = {
    "бухгалтерские услуги": [
        "бухгалтерские услуги", "бухгалтерских услуг", "услуги бухгалтера",
        "послуги бухгалтера", "послуги бухгалтера онлайн",
    ],
    "бухгалтерское сопровождение": [
        "бухгалтерское сопровождение", "бухгалтерского сопровождения",
        "сопровождение фоп", "сопровождение бизнеса",
    ],
    "бухгалтерское обслуживание": [
        "бухгалтерское обслуживание", "бухгалтерского обслуживания",
        "обслуживание юридических лиц", "бухгалтерское обслуживание юридических лиц",
    ],
    "ведение бухгалтерии": [
        "ведение бухгалтерии", "ведение бухгалтерского учета", "ведения бухгалтерии",
        "ведение учета", "бухгалтерский учет",
    ],
    "бухгалтерский аутсорсинг": [
        "бухгалтерский аутсорсинг", "аутсорсинг бухгалтерии", "бухгалтерия на аутсорсе",
    ],
    "налоговая отчетность": [
        "налоговая отчетность", "сдача отчетности", "подача отчетности",
        "налоговые отчеты", "отчетность фоп",
    ],
    "бухгалтер для ФОП": [
        "бухгалтер для фоп", "бухгалтерия фоп", "бухгалтерские услуги для фоп",
        "бухгалтерское сопровождение фоп",
    ],
    "искусственный интеллект": [
        "искусственный интеллект", "искусственного интеллекта", "искусственным интеллектом",
        "искусственному интеллекту", "искусственном интеллекте", "системы искусственного интеллекта",
        "технологии искусственного интеллекта",
    ],
    "машинное обучение": [
        "машинное обучение", "машинного обучения", "машинным обучением", "машинному обучению",
        "алгоритмы машинного обучения",
    ],
    "глубокое обучение": [
        "глубокое обучение", "глубокого обучения", "глубоким обучением",
    ],
    "нейронные сети": [
        "нейронные сети", "нейронных сетей", "нейронными сетями", "искусственные нейронные сети",
    ],
    "обработка естественного языка": [
        "обработка естественного языка", "обработки естественного языка", "обработку естественного языка",
        "обработкой естественного языка",
    ],
    "генеративный искусственный интеллект": [
        "генеративный искусственный интеллект", "генеративного искусственного интеллекта",
        "генеративным искусственным интеллектом",
    ],
    "artificial intelligence": [
        "artificial intelligence", "ai technology", "ai system", "ai systems",
    ],
}


@dataclass
class KeywordItem:
    phrase: str
    normalized: str
    score: float
    occurrences: int
    documents_count: int
    found_in_titles: int = 0
    found_in_h1: int = 0
    found_in_headings: int = 0
    urls: list[str] = field(default_factory=list)
    kind: str = "secondary"
    comment: str = ""


@dataclass
class RejectedPhrase:
    phrase: str
    reason: str
    source: str = ""


class KeywordExtractor:
    def __init__(
        self,
        min_n: int = 2,
        max_n: int = 4,
        max_keywords: int = 120,
        language: str = "ru",
        reduce_wikipedia_weight: bool = True,
    ):
        self.min_n = min_n
        self.max_n = max_n
        self.max_keywords = max_keywords
        self.language = language
        self.reduce_wikipedia_weight = reduce_wikipedia_weight
        self.lemmatizer = Lemmatizer()
        self.rejected: list[RejectedPhrase] = []

    def extract_aggregate(self, query: str, articles: list[ParsedArticle]) -> list[KeywordItem]:
        self.rejected = []
        phrase_stats: dict[str, dict] = defaultdict(lambda: {
            "surface": Counter(),
            "occurrences": 0,
            "documents": set(),
            "title_hits": 0,
            "h1_hits": 0,
            "heading_hits": 0,
            "urls": set(),
        })

        for article in articles:
            if article.error or not article.text:
                continue

            source_weight = self._source_weight(article.final_url)
            text_phrases = self._extract_phrases(article.text, source=article.final_url)

            title_phrases = set(self._extract_phrases(article.title, source=article.final_url).keys())
            h1_phrases = set(self._extract_phrases(article.h1, source=article.final_url).keys())
            heading_phrases = set(self._extract_phrases(" ".join([*article.h2, *article.h3]), source=article.final_url).keys())

            for phrase, count in text_phrases.items():
                normalized = self._canonical_normalized(phrase)
                phrase_stats[normalized]["surface"][phrase] += count
                phrase_stats[normalized]["occurrences"] += int(count * source_weight)
                phrase_stats[normalized]["documents"].add(article.final_url)
                phrase_stats[normalized]["urls"].add(article.final_url)

            for phrase in title_phrases:
                normalized = self._canonical_normalized(phrase)
                if normalized in phrase_stats:
                    phrase_stats[normalized]["title_hits"] += 1

            for phrase in h1_phrases:
                normalized = self._canonical_normalized(phrase)
                if normalized in phrase_stats:
                    phrase_stats[normalized]["h1_hits"] += 1

            for phrase in heading_phrases:
                normalized = self._canonical_normalized(phrase)
                if normalized in phrase_stats:
                    phrase_stats[normalized]["heading_hits"] += 1

        query_normalized = self.lemmatizer.normalize_phrase(query)
        query_terms = set(self.lemmatizer.normalize_phrase(query).split())
        items = []

        # Добавляем основной запрос всегда.
        items.append(KeywordItem(
            phrase=query,
            normalized=query_normalized,
            score=9999,
            occurrences=0,
            documents_count=0,
            kind="main",
            comment="Основной запрос задан пользователем.",
        ))

        for normalized, stat in phrase_stats.items():
            best_phrase = self._best_surface(stat["surface"])
            valid, reason = self._validate_final_phrase(best_phrase, normalized)
            if not valid:
                self._reject(best_phrase, reason, "final")
                continue

            docs_count = len(stat["documents"])
            occurrences = stat["occurrences"]
            title_hits = stat["title_hits"]
            h1_hits = stat["h1_hits"]
            heading_hits = stat["heading_hits"]

            phrase_terms = set(normalized.split())
            query_overlap = len(query_terms & phrase_terms)

            score = (
                occurrences * 1.0
                + docs_count * 6.0
                + title_hits * 8.0
                + h1_hits * 8.0
                + heading_hits * 4.0
                + query_overlap * 3.0
            )

            kind = self._classify(best_phrase, normalized, query_overlap, title_hits, h1_hits, heading_hits)
            comment = self._comment(kind, docs_count, title_hits, h1_hits, heading_hits)

            items.append(KeywordItem(
                phrase=best_phrase,
                normalized=normalized,
                score=round(score, 2),
                occurrences=occurrences,
                documents_count=docs_count,
                found_in_titles=title_hits,
                found_in_h1=h1_hits,
                found_in_headings=heading_hits,
                urls=sorted(stat["urls"]),
                kind=kind,
                comment=comment,
            ))

        items = sorted(items, key=lambda item: item.score, reverse=True)
        return items[: self.max_keywords]

    def _extract_phrases(self, text: str, source: str = "") -> Counter:
        raw_tokens = self.lemmatizer.tokens(text)
        counter = Counter()

        # Именованные SEO-сущности ищем как точные шаблоны и как варианты склонений.
        lower_text = (text or "").lower().replace("ё", "е")

        for canonical, variants in ENTITY_VARIANTS.items():
            total_count = 0
            for variant in variants:
                total_count += lower_text.count(variant)
            if total_count > 0:
                counter[canonical] += total_count

        for entity in ENTITY_PATTERNS:
            count = lower_text.count(entity)
            if count > 0:
                counter[ENTITY_PATTERNS[entity]] += count

        for n in range(self.min_n, self.max_n + 1):
            for index in range(0, len(raw_tokens) - n + 1):
                chunk = raw_tokens[index:index + n]
                if not chunk:
                    continue

                phrase = " ".join(chunk)
                valid, reason = self._validate_raw_phrase(chunk, phrase)
                if not valid:
                    self._reject(phrase, reason, source)
                    continue

                counter[phrase] += 1

        return counter

    def _validate_raw_phrase(self, chunk: list[str], phrase: str) -> tuple[bool, str]:
        lower = phrase.lower()

        if lower in BAD_EXACT:
            return False, "точное совпадение с мусорной фразой"

        if any(fragment in lower for fragment in BAD_FRAGMENTS):
            return False, "служебный или технический фрагмент"

        first = chunk[0].lower()
        last = chunk[-1].lower()

        # Вопросы типа "что такое ..." оставляем.
        if first in QUESTION_WORDS:
            if lower.startswith(("что такое ", "как работает ", "где используется ", "чем отличается ", "what is ", "how does ")):
                return True, ""
            return False, "фраза начинается с вопросительного/служебного слова, но не похожа на SEO-вопрос"

        if first in BAD_START:
            return False, "плохое начало фразы"

        if last in BAD_END:
            return False, "плохое окончание фразы"

        useful = [token for token in chunk if token not in STOPWORDS and token not in QUESTION_WORDS and len(token) > 2]
        if len(useful) < max(1, math.ceil(len(chunk) / 2)):
            return False, "мало полезных слов"

        # Короткие пары с предлогами/союзами почти всегда мусор:
        # "интеллекта в", "обучение и", "на основе", "с помощью".
        if len(chunk) <= 2 and any(token in STOPWORDS or token in QUESTION_WORDS for token in chunk):
            return False, "короткая фраза со служебным словом"

        # Грубый фильтр обрывков склонений.
        if lower.endswith(("ого", "его", "ому", "ему")) and len(chunk) <= 2:
            return False, "похоже на грамматический обрывок"

        return True, ""

    def _validate_final_phrase(self, phrase: str, normalized: str) -> tuple[bool, str]:
        lower = phrase.lower().strip()
        tokens = lower.split()
        norm_tokens = normalized.split()

        if not lower or len(tokens) < 2:
            return False, "слишком короткая финальная фраза"

        if lower in BAD_EXACT or normalized in BAD_EXACT:
            return False, "мусорная финальная фраза"

        if any(fragment in lower for fragment in BAD_FRAGMENTS):
            return False, "служебный фрагмент"

        if tokens[0] in BAD_START and not lower.startswith(("что такое", "как работает", "где используется", "чем отличается")):
            return False, "плохое начало финальной фразы"

        service_words = STOPWORDS | QUESTION_WORDS | BAD_END | BAD_START
        if tokens[-1] in service_words:
            return False, "плохое окончание финальной фразы"

        if len(tokens) <= 2 and any(token in service_words for token in tokens):
            # Исключение: точные сущности вроде "машинное обучение".
            if normalized not in ENTITY_VARIANTS and phrase.lower() not in ENTITY_PATTERNS.values():
                return False, "короткая финальная фраза со служебным словом"

        if norm_tokens and norm_tokens[-1] in BAD_END:
            return False, "плохое нормализованное окончание"

        bad_patterns = (
            r"\bтакое\s+искусствен",
            r"\bобработ\w*\s+естественн\w*$",
            r"\bобласти\s+искусствен",
            r"\bкак\s+они\b",
            r"\bтаких\s+как\b",
            r"\bчто\s+представляет\b",
            r"\bинтеллект\s+ии\b",
            r"\bии\s+как\b",
        )
        for pattern in bad_patterns:
            if re.search(pattern, lower):
                return False, "регулярное правило мусорной фразы"

        return True, ""

    def _canonical_normalized(self, phrase: str) -> str:
        lower = phrase.lower().replace("ё", "е")

        for canonical, variants in ENTITY_VARIANTS.items():
            for variant in variants:
                if variant in lower:
                    return canonical

        for entity in ENTITY_PATTERNS:
            if entity in lower:
                return ENTITY_PATTERNS[entity]

        return self.lemmatizer.normalize_phrase(phrase)

    def _best_surface(self, surfaces: Counter) -> str:
        if not surfaces:
            return ""

        def quality(item):
            phrase, count = item
            tokens = phrase.split()
            score = count
            if phrase in ENTITY_PATTERNS.values():
                score += 100
            if phrase.startswith(("что такое", "как работает", "где используется", "чем отличается")):
                score += 50
            if tokens and tokens[0] in BAD_START:
                score -= 100
            if tokens and tokens[-1] in BAD_END:
                score -= 100
            return score

        return max(surfaces.items(), key=quality)[0]

    def _classify(self, phrase: str, normalized: str, query_overlap: int, title_hits: int, h1_hits: int, heading_hits: int) -> str:
        lower = phrase.lower()

        if phrase.startswith(("что ", "как ", "где ", "чем ", "почему ", "what ", "how ", "where ", "why ")):
            return "faq"

        commercial_markers = (
            "цена", "стоимость", "купить", "заказать", "услуги", "консультация",
            "тариф", "оплата", "платный", "бесплатный", "онлайн",
        )
        if any(marker in lower for marker in commercial_markers):
            return "commercial"

        if normalized in {self.lemmatizer.normalize_phrase(value) for value in ENTITY_PATTERNS.values()}:
            return "entity"

        if query_overlap >= 2 or title_hits or h1_hits:
            return "secondary"

        if heading_hits:
            return "topic"

        return "lsi"

    def _comment(self, kind: str, docs_count: int, title_hits: int, h1_hits: int, heading_hits: int) -> str:
        parts = []
        if kind == "main":
            return "Основной запрос."
        if docs_count:
            parts.append(f"найдено у {docs_count} конкурентов")
        if title_hits:
            parts.append(f"есть в Title у {title_hits}")
        if h1_hits:
            parts.append(f"есть в H1 у {h1_hits}")
        if heading_hits:
            parts.append(f"есть в H2/H3 у {heading_hits}")
        return "; ".join(parts)

    def _source_weight(self, url: str) -> float:
        if self.reduce_wikipedia_weight and "wikipedia.org" in (url or "").lower():
            return 0.45
        return 1.0

    def _reject(self, phrase: str, reason: str, source: str = "") -> None:
        if not phrase or len(phrase) > 120:
            return
        self.rejected.append(RejectedPhrase(phrase=phrase, reason=reason, source=source))
