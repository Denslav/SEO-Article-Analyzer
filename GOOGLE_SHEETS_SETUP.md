# Google Sheets

В `config.yml` можно включить экспорт в Google Таблицу:

```yaml
google_sheets:
  enabled: true
  service_account_json: "service-account.json"
  spreadsheet_url: ""
  create_title: "SEO Article Analyzer Report v4"
  share_with_email: "your-email@gmail.com"
```

## Что нужно сделать

1. Создать проект в Google Cloud.
2. Включить Google Sheets API.
3. Создать Service Account.
4. Скачать JSON-ключ.
5. Положить файл рядом с `main.py`.
6. Указать путь к JSON в `config.yml`.

Если используешь существующую таблицу, расшарь её на email сервисного аккаунта.
