# SEO Article Analyzer v6.2

A program that analyzes articles from the Google TOP results for a specified query and generates an SEO report.

* Strict key phrase validator.
* Clean `Clean SEO Core` sheet.
* Working `Rejected Phrases` sheet with reasons for removal.
* Cleaner FAQ.
* Rejection of English FAQ questions when `language: ru` is selected.
* Human-friendly article structure.
* Transformation dictionary:

  * `обработка естественного языка` → `Natural Language Processing and Other AI Technologies`
  * `машинное обучение` → `Machine Learning, Neural Networks, and Deep Learning`
* Lightweight RU/UA/EN lemmatization without heavy libraries.
* Reduced influence of Wikipedia if `reduce_wikipedia_weight` is enabled.

## Installation

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Launch

```powershell
py main.py --config config.yml
```

## Report

The file will appear here:

```text
output/seo_article_report_v4.xlsx
```

## Report Sheets

* `Final SEO Brief` — ready-to-use SEO brief.
* `Clean SEO Core` — clean semantic core.
* `Rejected Phrases` — removed phrases and the reasons for removal.
* `Summary` — summary.
* `SERP Analysis` — analysis of URLs from the Google TOP results.
* `Keywords Raw` — raw keywords.
* `Keyword Groups` — keyword groups by lemmas.
* `Structure` — article structure.
* `Meta` — H1, Title, Description, slug.
* `FAQ` — cleaned questions.
* `Competitor Headings` — competitors’ headings.
