
from __future__ import annotations

import re
from collections import Counter

from seo_article_analyzer.core.keyword_extractor import KeywordItem


class HumanStructureBuilder:
    """
    Универсальный построитель структуры.
    Никаких зашитых тем типа ИИ/бухгалтерии.
    Структура строится по:
    - основному запросу;
    - интенту;
    - частым H2/H3 конкурентов;
    - чистому ядру.
    """

    def __init__(self, language: str = "ru"):
        self.language = language

    def build(self, query: str, keywords: list[KeywordItem], competitor_headings: list[str]) -> list[dict]:
        intent = self.detect_intent(query=query, keywords=keywords, headings=competitor_headings)
        page_type = self.detect_page_type(query=query, keywords=keywords, headings=competitor_headings)

        if intent == "commercial":
            return self._commercial_structure(
                query=query,
                keywords=keywords,
                competitor_headings=competitor_headings,
                page_type=page_type,
            )

        if intent == "mixed":
            return self._mixed_structure(
                query=query,
                keywords=keywords,
                competitor_headings=competitor_headings,
                page_type=page_type,
            )

        return self._informational_structure(
            query=query,
            keywords=keywords,
            competitor_headings=competitor_headings,
            page_type=page_type,
        )

    def detect_intent(self, query: str, keywords: list[KeywordItem], headings: list[str]) -> str:
        q = query.lower()
        text = " ".join([q, *[item.phrase.lower() for item in keywords[:40]], *[h.lower() for h in headings[:80]]])

        commercial_markers = (
            "купить", "заказать", "цена", "цены", "стоимость", "стоимост", "тариф", "тарифы",
            "услуга", "услуги", "сервис", "под ключ", "консультация", "стоимость", "прайс",
            "заказать", "оформить", "доставка", "оплата", "аренда", "ремонт", "установка",
            "монтаж", "аутсорсинг", "сопровождение", "обслуживание",
            "послуга", "послуги", "ціна", "вартість", "замовити", "купити",
            "price", "pricing", "cost", "buy", "order", "service", "services", "hire",
        )

        info_markers = (
            "что такое", "как ", "почему", "зачем", "когда", "где", "инструкция",
            "руководство", "гайд", "обзор", "виды", "примеры", "разница", "отличия",
            "как выбрать", "что выбрать", "плюсы", "минусы",
            "what is", "how to", "guide", "review", "examples", "difference",
        )

        commercial_score = sum(text.count(marker) for marker in commercial_markers)
        info_score = sum(text.count(marker) for marker in info_markers)

        # Запрос важнее текста конкурентов
        if any(marker in q for marker in commercial_markers):
            commercial_score += 8
        if any(marker in q for marker in info_markers):
            info_score += 8

        if commercial_score >= info_score + 4:
            return "commercial"
        if info_score >= commercial_score + 4:
            return "informational"
        if commercial_score >= 4 and info_score >= 3:
            return "mixed"

        return "informational"

    def detect_page_type(self, query: str, keywords: list[KeywordItem], headings: list[str]) -> str:
        q = query.lower()
        text = " ".join([q, *[item.phrase.lower() for item in keywords[:40]], *[h.lower() for h in headings[:80]]])

        if any(marker in text for marker in ("цена", "цены", "стоимость", "тариф", "прайс", "pricing", "price", "cost")):
            return "price_service"
        if any(marker in q for marker in ("услуга", "услуги", "service", "services", "послуга", "послуги")):
            return "service"
        if any(marker in q for marker in ("купить", "заказать", "buy", "order", "купити", "замовити")):
            return "commercial_landing"
        if any(marker in q for marker in ("как выбрать", "лучшие", "топ", "обзор", "review", "best")):
            return "review"
        if any(marker in q for marker in ("что такое", "как ", "почему", "зачем", "what is", "how to")):
            return "article"

        return "article"

    def _commercial_structure(
        self,
        query: str,
        keywords: list[KeywordItem],
        competitor_headings: list[str],
        page_type: str,
    ) -> list[dict]:
        structure = [
            self._row("H1", self._cap(query), [query], "Подтвердить релевантность коммерческому запросу.", "Основной запрос задан пользователем."),
            self._row("Вступление", f"Кратко: что предлагает страница по запросу «{query}»", [query], "Быстро объяснить предложение, пользу и для кого услуга/товар.", "Коммерческий интент требует быстрого ответа и ценности."),
        ]

        # Берём реальные темы из конкурентов, но очищаем и не дублируем.
        structure.extend(self._competitor_heading_blocks(competitor_headings, keywords, max_blocks=5, commercial=True))

        # Универсальные коммерческие блоки, если их не дали конкуренты.
        generic_blocks = [
            self._row("H2", f"Что входит в {query}", [query], "Показать состав предложения и конкретные работы/условия.", "Коммерческие страницы должны раскрывать состав услуги/предложения."),
            self._row("H2", "Цены и условия", ["цена", "стоимость", "тарифы"], "Закрыть интент стоимости и условий сотрудничества.", "Для коммерческих запросов стоимость часто влияет на решение."),
            self._row("H2", "Кому подходит это предложение", [query], "Сегментировать аудиторию и показать релевантные сценарии.", "Помогает пользователю понять, подходит ли ему услуга/товар."),
            self._row("H2", "Преимущества и гарантии", ["преимущества", "гарантии"], "Снять возражения и показать отличие от конкурентов.", "Коммерческой странице нужен блок доверия."),
            self._row("H2", "Как проходит работа", ["этапы", "как заказать"], "Объяснить процесс обращения, заказа или сотрудничества.", "Пользователь должен понимать следующий шаг."),
            self._row("H2", "Частые вопросы", [query], "Закрыть вопросы перед заявкой.", "FAQ помогает снять возражения."),
            self._row("H2", "Как заказать", [query], "Подвести пользователя к целевому действию.", "Коммерческой странице нужен CTA-блок."),
        ]

        structure = self._append_missing_blocks(structure, generic_blocks, max_total=13)
        return structure

    def _mixed_structure(
        self,
        query: str,
        keywords: list[KeywordItem],
        competitor_headings: list[str],
        page_type: str,
    ) -> list[dict]:
        structure = [
            self._row("H1", self._cap(query), [query], "Подтвердить релевантность запросу.", "Основной запрос задан пользователем."),
            self._row("Вступление", "Краткий ответ и польза для пользователя", [query], "Сразу объяснить тему и показать практическую пользу.", "Смешанный интент требует и объяснения, и коммерческой конкретики."),
        ]

        structure.extend(self._competitor_heading_blocks(competitor_headings, keywords, max_blocks=6, commercial=False))

        generic_blocks = [
            self._row("H2", f"Что важно знать про {query}", [query], "Дать базовое понимание темы.", "Закрывает информационную часть интента."),
            self._row("H2", "Варианты, цены и условия", ["цены", "условия", query], "Закрыть коммерческую часть интента.", "В смешанном интенте цена/условия часто важны."),
            self._row("H2", "Как выбрать подходящий вариант", ["как выбрать", query], "Помочь пользователю принять решение.", "Полезно для запросов с выбором."),
            self._row("H2", "Частые вопросы", [query], "Закрыть дополнительные вопросы.", "FAQ расширяет семантику."),
            self._row("H2", "Вывод", [query], "Кратко подвести итог.", "Логическое завершение статьи."),
        ]
        return self._append_missing_blocks(structure, generic_blocks, max_total=13)

    def _informational_structure(
        self,
        query: str,
        keywords: list[KeywordItem],
        competitor_headings: list[str],
        page_type: str,
    ) -> list[dict]:
        structure = [
            self._row("H1", self._cap(query), [query], "Подтвердить релевантность основному запросу.", "Основной запрос задан пользователем."),
            self._row("Вступление", "Краткий ответ на основной запрос", [query], "Дать быстрый ответ в первых абзацах.", "Информационный интент требует быстрого объяснения."),
        ]

        structure.extend(self._competitor_heading_blocks(competitor_headings, keywords, max_blocks=7, commercial=False))

        generic_blocks = [
            self._row("H2", f"Что такое {query}", [query], "Раскрыть базовое определение.", "Если конкуренты не дали понятный блок определения, его стоит добавить."),
            self._row("H2", f"Как работает {query}", [query], "Объяснить принцип работы или механизм.", "Частый блок для информационных запросов."),
            self._row("H2", "Примеры и применение", ["примеры", "применение"], "Показать тему на практике.", "Примеры делают статью понятнее."),
            self._row("H2", "Преимущества и недостатки", ["плюсы", "минусы"], "Сбалансировать раскрытие темы.", "Полезно для экспертности."),
            self._row("H2", "Частые вопросы", [query], "Закрыть дополнительные вопросы.", "FAQ расширяет семантику."),
            self._row("H2", "Вывод", [query], "Кратко подвести итог.", "Логическое завершение статьи."),
        ]
        return self._append_missing_blocks(structure, generic_blocks, max_total=13)

    def _competitor_heading_blocks(self, headings: list[str], keywords: list[KeywordItem], max_blocks: int = 6, commercial: bool = False) -> list[dict]:
        clean_headings = []
        for heading in headings:
            cleaned = self._clean_heading(heading)
            if not cleaned:
                continue
            clean_headings.append(cleaned)

        counter = Counter(clean_headings)
        rows = []

        for heading, count in counter.most_common(30):
            if len(rows) >= max_blocks:
                break

            if self._is_bad_heading(heading):
                continue

            related_keywords = self._keywords_for_heading(heading, keywords)
            rows.append(self._row(
                "H2",
                heading,
                related_keywords,
                "Раскрыть подтему, которая встречается у конкурентов.",
                f"Похожий блок найден у конкурентов: {count} раз.",
            ))

        return rows

    def _append_missing_blocks(self, structure: list[dict], blocks: list[dict], max_total: int) -> list[dict]:
        existing = {self._normalize(item["heading"]) for item in structure}

        for block in blocks:
            norm = self._normalize(block["heading"])
            if norm in existing:
                continue

            # Не добавляем явные дубли по смыслу.
            duplicate = False
            for existing_heading in existing:
                if self._similar(existing_heading, norm):
                    duplicate = True
                    break
            if duplicate:
                continue

            structure.append(block)
            existing.add(norm)

            if len(structure) >= max_total:
                break

        return structure

    def _keywords_for_heading(self, heading: str, keywords: list[KeywordItem]) -> list[str]:
        heading_tokens = set(self._normalize(heading).split())
        result = []

        for item in keywords:
            item_tokens = set(self._normalize(item.phrase).split())
            if heading_tokens & item_tokens:
                result.append(item.phrase)
            if len(result) >= 5:
                break

        return result or []

    def _clean_heading(self, heading: str) -> str:
        heading = re.sub(r"\s+", " ", heading or "").strip()
        heading = heading.strip(":-–—|")
        return self._cap(heading)

    def _is_bad_heading(self, heading: str) -> bool:
        lower = heading.lower()
        if len(lower) < 8 or len(lower) > 120:
            return True

        bad_fragments = (
            "cookie", "privacy", "terms", "читать также", "смотрите также",
            "комментарии", "поделиться", "навигация", "личные инструменты",
            "править код", "источники", "примечания", "литература",
            "перейти к", "содержание", "footer", "header",
        )
        if any(fragment in lower for fragment in bad_fragments):
            return True

        return False

    def _similar(self, a: str, b: str) -> bool:
        a_tokens = set(a.split())
        b_tokens = set(b.split())
        if not a_tokens or not b_tokens:
            return False
        overlap = len(a_tokens & b_tokens) / max(len(a_tokens), len(b_tokens))
        return overlap >= 0.75

    def _normalize(self, text: str) -> str:
        text = (text or "").lower().replace("ё", "е")
        text = re.sub(r"[^a-zа-яіїєґ0-9]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _row(self, block_type: str, heading: str, keywords: list[str], purpose: str, reason: str) -> dict:
        return {
            "block_type": block_type,
            "heading": heading,
            "keywords": keywords,
            "purpose": purpose,
            "reason": reason,
        }

    def _cap(self, text: str) -> str:
        text = (text or "").strip()
        return text[:1].upper() + text[1:] if text else text
