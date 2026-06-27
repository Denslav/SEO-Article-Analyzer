from __future__ import annotations

import re
from datetime import datetime

from seo_article_analyzer.core.faq_cleaner import FAQCleaner
from seo_article_analyzer.core.keyword_extractor import KeywordExtractor, KeywordItem, RejectedPhrase
from seo_article_analyzer.core.parser import ParsedArticle
from seo_article_analyzer.core.seo_structure import HumanStructureBuilder


class ReportBuilder:
    def __init__(self, config: dict):
        self.config = config
        self.language = config.get("language", "ru")
        analysis = config.get("analysis", {})
        self.max_clean_core = analysis.get("max_clean_core", 60)

        self.keyword_extractor = KeywordExtractor(
            min_n=analysis.get("min_phrase_length", 2),
            max_n=analysis.get("max_phrase_length", 4),
            max_keywords=analysis.get("max_keywords", 120),
            language=self.language,
            reduce_wikipedia_weight=analysis.get("reduce_wikipedia_weight", True),
        )
        self.faq_cleaner = FAQCleaner(
            language=self.language,
            reject_foreign=analysis.get("reject_foreign_faq", True),
            max_per_url=analysis.get("max_questions_per_url", 4),
        )
        self.structure_builder = HumanStructureBuilder(language=self.language)

    def build(self, query: str, articles: list[ParsedArticle]) -> dict[str, list[list]]:
        keywords = self.keyword_extractor.extract_aggregate(query=query, articles=articles)
        self.current_query = query.lower().strip()
        clean_core = self._clean_core(keywords)
        faq = self.faq_cleaner.clean(articles)
        headings = [heading for article in articles for heading in [*article.h2, *article.h3]]
        structure = self.structure_builder.build(query=query, keywords=clean_core, competitor_headings=headings)
        meta = self._build_meta(query=query, articles=articles, clean_core=clean_core)
        seo_brief = self._final_seo_brief(query=query, meta=meta, clean_core=clean_core, structure=structure, articles=articles, faq=faq)

        return {
            "Final SEO Brief": seo_brief,
            "Clean SEO Core": self._clean_core_sheet(clean_core),
            "Rejected Phrases": self._rejected_sheet(self.keyword_extractor.rejected),
            "Summary": self._summary_sheet(query, articles),
            "SERP Analysis": self._serp_analysis_sheet(query, articles),
            "Keywords Raw": self._keywords_sheet(keywords),
            "Keyword Groups": self._keyword_groups_sheet(keywords),
            "Structure": self._structure_sheet(structure),
            "Meta": self._meta_sheet(meta),
            "FAQ": self._faq_sheet(faq),
            "Competitor Headings": self._headings_sheet(articles),
        }


    def _final_seo_brief(
        self,
        query: str,
        meta: dict,
        clean_core: list[KeywordItem],
        structure: list[dict],
        articles: list[ParsedArticle],
        faq: list[dict],
    ) -> list[list]:
        ok = [article for article in articles if not article.error and article.status_code == 200]
        avg_words = int(sum(article.word_count for article in ok) / len(ok)) if ok else 0
        recommended_words = self._recommended_word_count(avg_words)

        main = [item.phrase for item in clean_core if item.kind == "main"][:1]
        secondary = [
            item.phrase for item in clean_core
            if item.kind in ("secondary", "topic", "commercial", "faq")
        ][:14]
        entities = [
            item.phrase for item in clean_core
            if item.kind == "entity"
        ][:14]
        lsi = self._final_lsi_terms(clean_core)[:14]
        faq_questions = [item["question"] for item in faq[:10]]

        rows = [
            ["Блок", "Значение"],
            ["Основной запрос", query],
            ["Интент", meta.get("intent", "")],
            ["Рекомендуемый H1", meta["h1"]],
            ["Рекомендуемый Title", meta["title"]],
            ["Рекомендуемый Meta Description", meta["description"]],
            ["Рекомендуемый slug", meta["slug"]],
            ["Рекомендуемый объём статьи", recommended_words],
            ["Основной ключ", ", ".join(main) or query],
            ["Дополнительные ключи", "\n".join(secondary)],
            ["Сущности / термины", "\n".join(entities)],
            ["LSI / тематические слова", "\n".join(lsi)],
            ["FAQ-вопросы", "\n".join(faq_questions)],
            ["Структура статьи", "\n".join([f'{item["block_type"]}: {item["heading"]}' for item in structure])],
        ]

        return rows

    def _summary_sheet(self, query: str, articles: list[ParsedArticle]) -> list[list]:
        ok = [article for article in articles if not article.error and article.status_code == 200]
        word_counts = [article.word_count for article in ok]
        avg_words = round(sum(word_counts) / len(word_counts), 1) if word_counts else 0
        return [
            ["Параметр", "Значение"],
            ["Основной запрос", query],
            ["Регион", self.config.get("region", "")],
            ["Язык", self.language],
            ["Дата анализа", datetime.now().strftime("%Y-%m-%d %H:%M")],
            ["URL передано", len(articles)],
            ["URL успешно обработано", len(ok)],
            ["Среднее количество слов", avg_words],
            ["Минимум слов", min(word_counts) if word_counts else 0],
            ["Максимум слов", max(word_counts) if word_counts else 0],
        ]

    def _serp_analysis_sheet(self, query: str, articles: list[ParsedArticle]) -> list[list]:
        rows = [[
            "Запрос", "Позиция", "URL", "Финальный URL", "Status",
            "Title", "Meta Description", "H1", "Количество слов",
            "Количество H2", "Количество H3", "Ошибка"
        ]]
        for index, article in enumerate(articles, start=1):
            rows.append([
                query,
                index,
                article.url,
                article.final_url,
                article.status_code,
                article.title,
                article.meta_description,
                article.h1,
                article.word_count,
                len(article.h2),
                len(article.h3),
                article.error,
            ])
        return rows


    def _clean_core_sheet(self, clean_core: list[KeywordItem]) -> list[list]:
        rows = [[
            "Фраза",
            "Тип",
            "Нормализованная группа",
            "Приоритет",
            "Найдено у URL",
            "В Title",
            "В H1",
            "В H2/H3",
            "Комментарий",
        ]]

        for item in clean_core:
            rows.append([
                item.phrase,
                item.kind,
                item.normalized,
                item.score,
                item.documents_count,
                item.found_in_titles,
                item.found_in_h1,
                item.found_in_headings,
                item.comment,
            ])

        return rows

    def _rejected_sheet(self, rejected: list[RejectedPhrase]) -> list[list]:
        rows = [["Фраза", "Причина удаления", "Источник"]]
        seen = set()

        for item in rejected:
            key = (item.phrase.lower(), item.reason, item.source)
            if key in seen:
                continue
            seen.add(key)

            rows.append([
                item.phrase,
                item.reason,
                item.source,
            ])

            if len(rows) > 500:
                break

        return rows

    def _keywords_sheet(self, keywords: list[KeywordItem]) -> list[list]:
        rows = [[
            "Фраза",
            "Тип",
            "Нормализованная группа",
            "Score",
            "Повторы",
            "В скольких URL",
            "В Title",
            "В H1",
            "В H2/H3",
            "URL где найдено",
            "Комментарий",
        ]]

        for item in keywords:
            rows.append([
                item.phrase,
                item.kind,
                item.normalized,
                item.score,
                item.occurrences,
                item.documents_count,
                item.found_in_titles,
                item.found_in_h1,
                item.found_in_headings,
                "\n".join(item.urls),
                item.comment,
            ])

        return rows

    def _keyword_groups_sheet(self, keywords: list[KeywordItem]) -> list[list]:
        rows = [[
            "Нормализованная группа",
            "Лучшая фраза",
            "Тип",
            "Score",
            "Повторы",
            "Найдено у URL",
            "Комментарий",
        ]]

        for item in keywords:
            rows.append([
                item.normalized,
                item.phrase,
                item.kind,
                item.score,
                item.occurrences,
                item.documents_count,
                item.comment,
            ])

        return rows

    def _structure_sheet(self, structure: list[dict]) -> list[list]:
        rows = [[
            "Тип блока",
            "Рекомендуемый заголовок",
            "Ключевые слова",
            "Задача блока",
            "Основание",
        ]]

        for item in structure:
            rows.append([
                item.get("block_type", ""),
                item.get("heading", ""),
                ", ".join(item.get("keywords", [])),
                item.get("purpose", ""),
                item.get("reason", ""),
            ])

        return rows

    def _meta_sheet(self, meta: dict) -> list[list]:
        return [
            ["Поле", "Рекомендация", "Длина"],
            ["H1", meta.get("h1", ""), len(meta.get("h1", ""))],
            ["Title", meta.get("title", ""), len(meta.get("title", ""))],
            ["Meta Description", meta.get("description", ""), len(meta.get("description", ""))],
            ["Slug", meta.get("slug", ""), len(meta.get("slug", ""))],
            ["Intent", meta.get("intent", ""), ""],
        ]

    def _faq_sheet(self, faq: list[dict]) -> list[list]:
        rows = [["Вопрос", "Источник URL", "Комментарий"]]

        for item in faq:
            rows.append([
                item.get("question", ""),
                item.get("url", ""),
                item.get("comment", ""),
            ])

        return rows

    def _headings_sheet(self, articles: list[ParsedArticle]) -> list[list]:
        rows = [["Позиция", "URL", "Уровень", "Заголовок"]]

        for index, article in enumerate(articles, start=1):
            if article.h1:
                rows.append([index, article.final_url, "H1", article.h1])

            for heading in article.h2:
                rows.append([index, article.final_url, "H2", heading])

            for heading in article.h3:
                rows.append([index, article.final_url, "H3", heading])

        return rows

    def _clean_core(self, keywords: list[KeywordItem]) -> list[KeywordItem]:
        result = []
        seen = set()

        for item in keywords:
            if not self._is_final_keyword(item):
                continue

            normalized_key = self._display_normalized(item)
            if normalized_key in seen:
                continue

            item.normalized = normalized_key
            seen.add(normalized_key)
            result.append(item)

            if len(result) >= self.max_clean_core:
                break

        result = self._inject_query_based_keywords(result)
        return result[: self.max_clean_core]

    def _display_normalized(self, item: KeywordItem) -> str:
        # Не превращаем группы в странные корни. Для пользователя важнее человекочитаемая группа.
        if item.kind == "main":
            return item.phrase
        return item.normalized or item.phrase

    def _is_final_keyword(self, item: KeywordItem) -> bool:
        phrase = (item.phrase or "").lower().strip()
        tokens = phrase.split()

        if item.kind == "main":
            return True

        if len(tokens) < 2:
            return False

        # Убираем явные текстовые обрывки.
        service_words = {
            "и", "в", "во", "на", "с", "со", "к", "ко", "о", "об", "от", "по", "для",
            "как", "что", "это", "ли", "они", "она", "оно", "такой", "такая", "такие",
            "and", "or", "of", "to", "for", "with", "in", "on", "the",
        }

        if tokens[0] in service_words or tokens[-1] in service_words:
            return False

        if len(tokens) <= 2 and any(token in service_words for token in tokens):
            return False

        bad_fragments = (
            "на основе", "с помощью", "о том", "в области", "подход к",
            "данных и", "задач и", "для решения", "связанные с", "в себя",
            "и методов", "между", "разница между", "что вы ищете",
            "таких как", "как они", "представляет собой",
        )
        if any(fragment == phrase or fragment in phrase for fragment in bad_fragments):
            return False

        # LSI допускаем только если фраза найдена минимум у нескольких конкурентов.
        if item.kind == "lsi" and item.documents_count < 2:
            return False

        # Слишком слабые двухсловные фразы не берём, если это не сущность/коммерческий маркер/FAQ.
        if len(tokens) == 2 and item.kind not in ("entity", "commercial", "faq", "secondary", "topic"):
            return False

        return True

    def _inject_query_based_keywords(self, result: list[KeywordItem]) -> list[KeywordItem]:
        """
        Универсальные seed-запросы без привязки к теме.
        Мы не зашиваем ИИ/бухгалтерию. Берём только основной запрос и интент.
        """
        query = getattr(self, "current_query", "").strip()
        if not query:
            return result

        existing = {item.phrase.lower() for item in result}
        intent = self._detect_intent_from_text(query, " ".join(item.phrase for item in result))

        seeds: list[tuple[str, str]] = []

        if intent == "commercial":
            seeds = [
                (query, "main"),
                (f"{query} цена", "commercial"),
                (f"{query} стоимость", "commercial"),
                (f"{query} заказать", "commercial"),
                (f"{query} онлайн", "commercial"),
                (f"сколько стоит {query}", "faq"),
                (f"как выбрать {query}", "faq"),
            ]
        elif intent == "mixed":
            seeds = [
                (query, "main"),
                (f"что важно знать про {query}", "secondary"),
                (f"как выбрать {query}", "secondary"),
                (f"{query} цена", "commercial"),
                (f"сколько стоит {query}", "faq"),
            ]
        else:
            seeds = [
                (query, "main"),
                (f"что такое {query}", "secondary"),
                (f"как работает {query}", "secondary"),
                (f"примеры {query}", "secondary"),
                (f"виды {query}", "secondary"),
            ]

        score = 8500
        for phrase, kind in seeds:
            if phrase.lower() in existing:
                continue
            result.append(KeywordItem(
                phrase=phrase,
                normalized=phrase,
                score=score,
                occurrences=0,
                documents_count=0,
                kind=kind,
                comment="Добавлено как универсальная SEO-формулировка на основе основного запроса и интента.",
            ))
            existing.add(phrase.lower())
            score -= 1

        return result

    def _detect_intent_from_text(self, query: str, text: str) -> str:
        q = query.lower()
        haystack = f"{q} {text.lower()}"

        commercial_markers = (
            "услуги", "услуга", "цена", "цены", "стоимость", "тариф", "заказать",
            "купить", "консультация", "аутсорсинг", "сопровождение", "обслуживание",
            "послуги", "ціна", "вартість", "замовити", "service", "services",
            "price", "pricing", "cost", "buy", "order", "hire",
        )
        info_markers = (
            "что такое", "как ", "почему", "зачем", "где", "когда", "инструкция",
            "гайд", "обзор", "виды", "примеры", "what is", "how to", "guide",
        )

        commercial = sum(haystack.count(marker) for marker in commercial_markers)
        info = sum(haystack.count(marker) for marker in info_markers)

        if any(marker in q for marker in commercial_markers):
            commercial += 8
        if any(marker in q for marker in info_markers):
            info += 8

        if commercial >= info + 4:
            return "commercial"
        if info >= commercial + 4:
            return "informational"
        if commercial >= 4 and info >= 3:
            return "mixed"
        return "informational"

    def _final_lsi_terms(self, clean_core: list[KeywordItem]) -> list[str]:
        # Универсально берём сущности и частые тематические фразы из чистого ядра.
        terms = []
        for item in clean_core:
            if item.kind in ("entity", "topic", "lsi", "secondary"):
                phrase = item.phrase
                if phrase not in terms:
                    terms.append(phrase)
            if len(terms) >= 14:
                break
        return terms

    def _build_meta(self, query: str, articles: list[ParsedArticle], clean_core: list[KeywordItem]) -> dict:
        clean = query.strip()
        h1 = self._cap(clean)

        competitor_titles = [article.title for article in articles if article.title]
        competitor_descriptions = [article.meta_description for article in articles if article.meta_description]
        competitor_h1 = [article.h1 for article in articles if article.h1]
        competitor_h2 = [heading for article in articles for heading in article.h2[:8]]

        competitor_text = " ".join([*competitor_titles, *competitor_descriptions, *competitor_h1, *competitor_h2]).lower()
        intent = self._detect_intent_from_text(clean, competitor_text)

        title = self._build_competitor_based_title(
            query=clean,
            intent=intent,
            competitor_titles=competitor_titles,
            competitor_h1=competitor_h1,
            clean_core=clean_core,
        )

        description = self._build_competitor_based_description(
            query=clean,
            intent=intent,
            competitor_text=competitor_text,
            clean_core=clean_core,
        )

        return {
            "h1": h1,
            "title": self._fit_title(title, clean),
            "description": self._fit_description(description),
            "slug": self._slug(clean),
            "intent": intent,
        }

    def _build_competitor_based_title(self, query: str, intent: str, competitor_titles: list[str], competitor_h1: list[str], clean_core: list[KeywordItem]) -> str:
        text = " ".join([*competitor_titles, *competitor_h1]).lower()

        modifiers = []
        modifier_candidates = [
            ("цены", ("цена", "цены", "стоимость", "тариф", "прайс")),
            ("условия", ("условия", "как заказать", "этапы", "формат")),
            ("онлайн", ("онлайн", "удаленно", "remote")),
            ("в Украине", ("украина", "украине", "україна", "україні")),
            ("под ключ", ("под ключ",)),
            ("для бизнеса", ("для бизнеса", "для компан", "для компаний", "юридических лиц")),
            ("для ФОП", ("фоп", "фізичних осіб")),
        ]

        for label, markers in modifier_candidates:
            if any(marker in text for marker in markers):
                modifiers.append(label)

        # Ограничиваем, чтобы Title не был кашей.
        modifiers = modifiers[:2]

        if intent == "commercial":
            if modifiers:
                return f"{self._cap(query)}: {', '.join(modifiers)}"
            return f"{self._cap(query)}: цены и условия"

        if intent == "mixed":
            if modifiers:
                return f"{self._cap(query)}: {', '.join(modifiers)} и как выбрать"
            return f"{self._cap(query)}: как выбрать и что важно знать"

        # informational
        info_modifiers = []
        if any(marker in text for marker in ("что такое", "что это", "определение")):
            info_modifiers.append("что это")
        if any(marker in text for marker in ("как работает", "принцип", "этапы")):
            info_modifiers.append("как работает")
        if any(marker in text for marker in ("примеры", "виды", "плюсы", "минусы")):
            info_modifiers.append("примеры")

        if info_modifiers:
            return f"{self._cap(query)}: {', '.join(info_modifiers[:2])}"
        return f"{self._cap(query)}: что важно знать"

    def _build_competitor_based_description(self, query: str, intent: str, competitor_text: str, clean_core: list[KeywordItem]) -> str:
        topics = self._extract_description_topics(competitor_text, clean_core)

        if intent == "commercial":
            base_topics = topics or ["что входит", "цены", "условия", "как заказать"]
            return (
                f"{self._cap(query)}: {', '.join(base_topics[:5])}. "
                f"Сравните предложения, условия и выберите подходящий вариант."
            )

        if intent == "mixed":
            base_topics = topics or ["что важно знать", "цены", "условия", "как выбрать"]
            return (
                f"{self._cap(query)}: {', '.join(base_topics[:5])}. "
                f"Разбираем пользу, варианты, условия и частые вопросы."
            )

        base_topics = topics or ["основные понятия", "примеры", "преимущества", "частые вопросы"]
        return (
            f"Разбираем {query}: {', '.join(base_topics[:5])}. "
            f"Простое объяснение, важные нюансы и ответы на частые вопросы."
        )

    def _extract_description_topics(self, competitor_text: str, clean_core: list[KeywordItem]) -> list[str]:
        topics = []

        marker_map = [
            ("цены", ("цена", "цены", "стоимость", "тариф")),
            ("условия", ("условия", "формат", "этапы")),
            ("онлайн", ("онлайн", "удаленно")),
            ("для бизнеса", ("для бизнеса", "компаний", "юридических лиц")),
            ("для ФОП", ("фоп",)),
            ("преимущества", ("преимущества", "выгоды", "почему")),
            ("как выбрать", ("как выбрать", "выбор", "критерии")),
            ("примеры", ("примеры", "пример")),
            ("виды", ("виды", "типы")),
        ]

        for label, markers in marker_map:
            if any(marker in competitor_text for marker in markers):
                topics.append(label)

        for item in clean_core:
            if item.kind in ("entity", "secondary", "commercial") and item.phrase not in topics:
                phrase = item.phrase
                if len(phrase) <= 35:
                    topics.append(phrase)
            if len(topics) >= 6:
                break

        return topics[:6]

    def _fit_title(self, title: str, fallback_query: str) -> str:
        title = " ".join(title.split())
        if len(title) <= 70:
            return title
        title = title.replace(", условия", "").replace(", онлайн", "").replace(", под ключ", "")
        if len(title) <= 70:
            return title
        return self._cap(fallback_query)

    def _fit_description(self, description: str) -> str:
        description = " ".join(description.split())
        if len(description) <= 165:
            return description
        return description[:162].rstrip() + "..."

    def _recommended_word_count(self, avg_words: int) -> str:
        if avg_words <= 0:
            return "2500-3500 слов"
        low = max(1200, int(avg_words * 0.8))
        high = int(avg_words * 1.15)
        return f"{low}-{high} слов"

    def _cap(self, text: str) -> str:
        text = text.strip()
        return text[:1].upper() + text[1:] if text else text

    def _slug(self, text: str) -> str:
        mapping = {
            "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
            "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
            "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "c",
            "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu",
            "я": "ya", "і": "i", "ї": "yi", "є": "ye", "ґ": "g",
        }
        text = text.lower().strip()
        text = "".join(mapping.get(char, char) for char in text)
        text = re.sub(r"[^a-z0-9]+", "-", text)
        return text.strip("-")
