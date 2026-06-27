from __future__ import annotations

from typing import Any

import gspread


class GoogleSheetsExporter:
    def __init__(self, config: dict[str, Any]):
        self.config = config

    def export(self, report: dict[str, list[list]]) -> str:
        credentials_path = self.config.get("service_account_json")
        if not credentials_path:
            raise ValueError("Не указан путь к service_account_json.")

        client = gspread.service_account(filename=credentials_path)

        spreadsheet_url = self.config.get("spreadsheet_url")
        if spreadsheet_url:
            spreadsheet = client.open_by_url(spreadsheet_url)
        else:
            spreadsheet = client.create(self.config.get("create_title", "SEO Article Analyzer Report v4"))

        share_with_email = self.config.get("share_with_email")
        if share_with_email:
            spreadsheet.share(share_with_email, perm_type="user", role="writer")

        for sheet_name, rows in report.items():
            safe_name = self._safe_sheet_name(sheet_name)
            try:
                worksheet = spreadsheet.worksheet(safe_name)
                worksheet.clear()
            except Exception:
                worksheet = spreadsheet.add_worksheet(
                    title=safe_name,
                    rows=max(100, len(rows) + 10),
                    cols=max(20, len(rows[0]) if rows else 10),
                )

            if rows:
                worksheet.update(values=rows, range_name="A1")

            try:
                worksheet.freeze(rows=1)
            except Exception:
                pass

        return spreadsheet.url

    def _safe_sheet_name(self, name: str) -> str:
        for char in ["\\", "/", "*", "[", "]", ":", "?"]:
            name = name.replace(char, " ")
        return name[:100]
