from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from seo_article_analyzer.core.analyzer import ArticleAnalyzer
from seo_article_analyzer.core.report_builder import ReportBuilder
from seo_article_analyzer.exporters.excel_exporter import ExcelExporter
from seo_article_analyzer.exporters.google_sheets_exporter import GoogleSheetsExporter


def load_config(path: str) -> dict:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Файл конфигурации не найден: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SEO Article Analyzer v4: анализ статей из ТОПа Google и формирование SEO-ТЗ."
    )
    parser.add_argument("--config", default="config.yml", help="Путь к YAML-конфигу.")
    args = parser.parse_args()

    config = load_config(args.config)

    query = config.get("query", "").strip()
    urls = config.get("urls", [])

    if not query:
        raise ValueError("В config.yml не указан query.")
    if not urls:
        raise ValueError("В config.yml не указаны urls.")

    analyzer = ArticleAnalyzer(config=config)
    articles = analyzer.analyze_urls(query=query, urls=urls)

    builder = ReportBuilder(config=config)
    report = builder.build(query=query, articles=articles)

    xlsx_path = config.get("local_export", {}).get("xlsx_path", "output/seo_article_report_v4.xlsx")
    ExcelExporter().export(report=report, xlsx_path=xlsx_path)
    print(f"Локальный XLSX-отчёт создан: {xlsx_path}")

    sheets_config = config.get("google_sheets", {})
    if sheets_config.get("enabled"):
        exporter = GoogleSheetsExporter(config=sheets_config)
        sheet_url = exporter.export(report=report)
        print(f"Google Таблица создана/обновлена: {sheet_url}")


if __name__ == "__main__":
    main()
