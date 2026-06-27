from __future__ import annotations

import re


class FAQCleaner:
    def __init__(self, language: str = "ru", reject_foreign: bool = True, max_per_url: int = 4):
        self.language = language
        self.reject_foreign = reject_foreign
        self.max_per_url = max_per_url

    def clean(self, articles) -> list[dict]:
        rows = []
        seen = set()

        for article in articles:
            per_url = 0
            for question in article.questions:
                valid, reason = self._is_valid(question)
                if not valid:
                    continue

                norm = self._normalize(question)
                if norm in seen:
                    continue

                seen.add(norm)
                rows.append({
                    "question": question,
                    "url": article.final_url,
                    "comment": "Вопрос найден у конкурента.",
                })
                per_url += 1

                if per_url >= self.max_per_url:
                    break

        return rows

    def _is_valid(self, question: str) -> tuple[bool, str]:
        q = (question or "").strip()
        lower = q.lower()

        if len(q) < 10 or len(q) > 145:
            return False, "длина не подходит"

        bad_fragments = (
            "what will happen if", "can you explain to me why i get sick",
            "what causes what", "божиим", "творением", "насколько это обосновано",
            "doi", "isbn", "архивировано", "pmid", "цит", "источник",
            "—", "»", "«",
        )
        if any(fragment in lower for fragment in bad_fragments):
            return False, "похоже на цитату или мусор"

        if self.reject_foreign and self.language in ("ru", "uk"):
            latin_count = len(re.findall(r"[a-zA-Z]", q))
            cyr_count = len(re.findall(r"[а-яА-ЯёЁіІїЇєЄґҐ]", q))
            if latin_count > cyr_count:
                return False, "иностранный вопрос для RU/UA отчёта"

        starters_ru = (
            "что ", "как ", "где ", "когда ", "почему ", "зачем ", "какой ", "какая ",
            "какие ", "сколько ", "можно ли ", "чем ", "кто ",
        )
        starters_uk = (
            "що ", "як ", "де ", "коли ", "чому ", "який ", "яка ", "які ", "скільки ",
        )
        starters_en = (
            "what ", "how ", "where ", "when ", "why ", "which ", "can ", "is ", "are ",
        )

        allowed = starters_en if self.language == "en" else starters_ru + starters_uk
        if not lower.startswith(allowed):
            return False, "не начинается с нормального вопросительного слова"

        return True, ""

    def _normalize(self, question: str) -> str:
        return re.sub(r"\s+", " ", question.lower().strip().replace("?", ""))
