# ReaderBot Minimal Runtime

## What is this?

This is a minimal production package of your Business Card Reader Telegram bot.
It contains only the files needed to run the bot in cloud hosting (like DigitalOcean App Platform Worker).

The bot flow is:
1. User sends a business card photo in Telegram.
2. Bot downloads the image.
3. Bot sends the image to your Google Apps Script Web App URL.
4. Apps Script extracts contact details and returns JSON.
5. Bot normalizes data and replies in Telegram with extracted fields.

## Included files

- `bot.py` (entry point)
- `src/` (bot logic, config, extraction call, normalization)
- `requirements.txt` (Python dependencies)
- `runtime.txt` (Python runtime pin for production)
- `.gitignore`

## Environment variables

Required:
- `TELEGRAM_BOT_TOKEN`
- `APPS_SCRIPT_WEB_APP_URL`

Optional:
- `EMAIL_SUBJECT`
- `EMAIL_BODY`

## Run locally

```powershell
pip install -r requirements.txt
python bot.py
```

## Deploy on DigitalOcean App Platform

Use a **Worker** component (not Web Service).

- Build strategy: Buildpack
- Build command: `pip install -r requirements.txt`
- Run command: `python bot.py`
- Source directory: `bot-runtime-minimal`

Add environment variables in DigitalOcean app settings and redeploy.
