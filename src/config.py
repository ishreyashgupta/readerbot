import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv


load_dotenv()


def _unescape_env_text(value: str) -> str:
    return value.replace("\\r\\n", "\n").replace("\\n", "\n")


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    apps_script_url: str
    gemini_api_key: str
    gemini_model: str
    email_subject: str
    email_body: str
    email_user: str
    email_pass: str
    spreadsheet_name: str
    google_credentials_path: str


class ConfigError(ValueError):
    """Raised when required environment variables are missing."""


def get_settings() -> Settings:
    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        apps_script_url=(
            os.getenv("APPS_SCRIPT_WEB_APP_URL", "").strip()
            or os.getenv("APPS_SCRIPT_DEPLOYMENT_URL", "").strip()
            or "https://script.google.com/macros/s/AKfycby5vTivBuoHFKXGC_r5LgeC3VWKAMReWiYjR8hnl6gVYbdz4dj0AYHKDiqwczhHjyDo/exec"
        ),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip(),
        email_subject=os.getenv("EMAIL_SUBJECT", "Nice connecting with you!").strip() or "Nice connecting with you!",
        email_body=(
            _unescape_env_text(os.getenv("EMAIL_BODY", "").strip())
            or "Hi {name},\n\nIt was great connecting with you.\n\n"
            "We noticed you are working as {designation} at {company}.\n\n"
            "{profile_url}\n\nRegards,\nYour Name"
        ),
        email_user=os.getenv("EMAIL_USER", "").strip(),
        email_pass=os.getenv("EMAIL_PASS", "").strip(),
        spreadsheet_name=os.getenv("SPREADSHEET_NAME", "Leads").strip() or "Leads",
        google_credentials_path=os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json").strip() or "credentials.json",
    )


def validate_settings(settings: Settings) -> None:
    missing: List[str] = []

    if not settings.telegram_bot_token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not settings.apps_script_url:
        missing.append("APPS_SCRIPT_WEB_APP_URL")

    if missing:
        raise ConfigError(f"Missing required environment variables: {', '.join(missing)}")
