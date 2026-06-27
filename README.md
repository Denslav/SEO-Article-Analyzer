# SEO Article Analyzer v6.2

Программа анализирует статьи из ТОПа Google по заданному запросу и формирует SEO-отчёт.

## Что улучшено в v4.3

- Строгий валидатор ключевых фраз.
- Чистая вкладка `Clean SEO Core`.
- Рабочая вкладка `Rejected Phrases` с причинами удаления.
- Более чистый FAQ.
- Отбраковка английских FAQ при `language: ru`.
- Человеческая структура статьи.
- Словарь преобразований:
  - `обработка естественного языка` → `Обработка естественного языка и другие технологии ИИ`
  - `машинное обучение` → `Машинное обучение, нейросети и глубокое обучение`
- Лёгкая лемматизация RU/UA/EN без тяжёлых библиотек.
- Уменьшение влияния Wikipedia, если включено `reduce_wikipedia_weight`.

## Установка

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Запуск

```powershell
    py main.py --config config.yml
```

## Отчёт

Файл появится здесь:

```text
output/seo_article_report_v4.xlsx
```

## Вкладки отчёта

- `Final SEO Brief` — готовое SEO-ТЗ.
- `Clean SEO Core` — чистое ядро.
- `Rejected Phrases` — удалённые фразы и причины.
- `Summary` — сводка.
- `SERP Analysis` — анализ URL из ТОПа.
- `Keywords Raw` — сырые ключи.
- `Keyword Groups` — группы по леммам.
- `Structure` — структура статьи.
- `Meta` — H1, Title, Description, slug.
- `FAQ` — очищенные вопросы.
- `Competitor Headings` — заголовки конкурентов.
