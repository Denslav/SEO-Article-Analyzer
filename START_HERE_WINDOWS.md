# Быстрый старт на Windows

## 1. Распакуй архив

Например:

```text
D:\Seo\SEO Tools\Scripts\seo_article_analyzer_v4
```

## 2. Запусти установку

Двойной клик по файлу:

```text
install_windows.bat
```

## 3. Отредактируй config.yml

Укажи:

```yaml
query: "искусственный интеллект простыми словами"

urls:
  - "https://site1.com/article/"
  - "https://site2.com/article/"
```

## 4. Запусти анализ

Двойной клик по файлу:

```text
run_windows.bat
```

## 5. Где будет отчёт

```text
output\seo_article_report_v4.xlsx
```

## Если bat не работает

Открой PowerShell в папке проекта и выполни:

```powershell
.\.venv\Scripts\python.exe main.py --config config.yml
```
