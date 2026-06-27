from __future__ import annotations

import re


RU_UA_ENDINGS = (
    "иями", "ями", "ами", "его", "ого", "ему", "ому", "ыми", "ими",
    "ая", "яя", "ое", "ее", "ые", "ие", "ого", "его", "ому", "ему",
    "ой", "ей", "ый", "ий", "ым", "им", "ом", "ем", "ах", "ях",
    "ую", "юю", "а", "я", "ы", "и", "е", "у", "ю", "о", "ом", "ем",
    "ів", "ов", "ев", "ою", "ею", "ість", "ости", "ості",
)

RU_UA_EXCEPTIONS = {
    # Частые SEO-термины лучше сохранять в нормальной форме, а не обрезать до корня.
    "искусственный": "искусственный",
    "искусственная": "искусственный",
    "искусственное": "искусственный",
    "искусственные": "искусственный",
    "естественный": "естественный",
    "естественная": "естественный",
    "естественное": "естественный",
    "естественные": "естественный",
    "машинное": "машинное",
    "машинный": "машинное",
    "машинного": "машинное",
    "глубокое": "глубокое",
    "глубокий": "глубокое",
    "глубокого": "глубокое",
    "нейронные": "нейронные",
    "нейронный": "нейронные",
    "генеративный": "генеративный",
    "генеративного": "генеративный",
    "человеческий": "человеческий",
    "человеческого": "человеческий",
    "искусственного": "искусственный",
    "искусственным": "искусственный",
    "искусственному": "искусственный",
    "искусственном": "искусственный",
    "интеллекта": "интеллект",
    "интеллектом": "интеллект",
    "интеллекту": "интеллект",
    "интеллекте": "интеллект",
    "обработку": "обработка",
    "обработки": "обработка",
    "обработкой": "обработка",
    "естественного": "естественный",
    "естественном": "естественный",
    "языка": "язык",
    "языком": "язык",
    "обучения": "обучение",
    "обучением": "обучение",
    "машинного": "машинный",
    "машинном": "машинный",
    "нейронные": "нейронный",
    "нейронных": "нейронный",
    "сетей": "сеть",
    "сети": "сеть",
    "данных": "данные",
    "алгоритмов": "алгоритм",
    "моделей": "модель",
    "технологий": "технология",
    "приложений": "приложение",
}

EN_EXCEPTIONS = {
    "artificial": "artificial",
    "intelligence": "intelligence",
    "technologies": "technology",
    "technology": "technology",
    "models": "model",
    "model": "model",
    "systems": "system",
    "system": "system",
    "uses": "use",
    "using": "use",
    "used": "use",
    "trained": "train",
    "training": "train",
    "machines": "machine",
    "learning": "learning",
    "networks": "network",
    "applications": "application",
    "examples": "example",
    "tools": "tool",
    "questions": "question",
}


class Lemmatizer:
    def normalize_token(self, token: str) -> str:
        token = token.lower().replace("ё", "е").strip()
        if not token:
            return token

        if re.search(r"[a-z]", token):
            return self._normalize_en(token)

        return self._normalize_ru_ua(token)

    def normalize_phrase(self, phrase: str) -> str:
        tokens = self.tokens(phrase)
        lemmas = [self.normalize_token(token) for token in tokens]
        return " ".join([lemma for lemma in lemmas if lemma])

    def tokens(self, text: str) -> list[str]:
        text = (text or "").lower().replace("ё", "е")
        return re.findall(r"[a-zа-яіїєґ0-9]+", text, flags=re.IGNORECASE)

    def _normalize_en(self, token: str) -> str:
        if token in EN_EXCEPTIONS:
            return EN_EXCEPTIONS[token]

        if len(token) > 5 and token.endswith("ies"):
            return token[:-3] + "y"
        if len(token) > 5 and token.endswith("ing"):
            base = token[:-3]
            if len(base) > 3 and base[-1] == base[-2]:
                base = base[:-1]
            return base
        if len(token) > 4 and token.endswith("ed"):
            return token[:-2]
        if len(token) > 4 and token.endswith("es"):
            return token[:-2]
        if len(token) > 3 and token.endswith("s"):
            return token[:-1]

        return token

    def _normalize_ru_ua(self, token: str) -> str:
        if token in RU_UA_EXCEPTIONS:
            return RU_UA_EXCEPTIONS[token]

        if len(token) <= 4:
            return token

        for ending in sorted(RU_UA_ENDINGS, key=len, reverse=True):
            if token.endswith(ending) and len(token) - len(ending) >= 4:
                return token[: -len(ending)]

        return token
