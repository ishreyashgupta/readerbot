import logging
import os
import tempfile
from typing import Dict

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.config import ConfigError, get_settings, validate_settings
from src.gemini import extract_data
from src.utils import normalize_extracted_data


LOGGER = logging.getLogger(__name__)


def _format_summary(data: Dict[str, str]) -> str:
    phone_lines = []
    for key, label in (
        ("number1", "Number1"),
        ("number2", "Number2"),
        ("number3", "Number3"),
        ("number4", "Number4"),
    ):
        value = data.get(key, "") or ""
        if value:
            phone_lines.append(f"{label}: {value}")

    if not phone_lines:
        fallback_phone = data.get("phone", "") or ""
        if fallback_phone:
            phone_lines.append(f"Number1: {fallback_phone}")

    summary = [
        "Extracted details:",
        f"Name: {data.get('name', '') or 'N/A'}",
        f"Designation: {data.get('designation', '') or 'N/A'}",
        f"Company: {data.get('company', '') or 'N/A'}",
        f"Email: {data.get('email', '') or 'N/A'}",
    ]

    if phone_lines:
        summary.append("Phone Numbers:")
        summary.extend(phone_lines)
    else:
        summary.append("Phone Numbers: N/A")

    return "\n".join(summary)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    await update.message.reply_text("Send a business card image to extract contact details.")


async def handle_non_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    await update.message.reply_text("Please send an image of a business card.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context

    if not update.message or not update.message.photo:
        return

    photo = update.message.photo[-1]
    telegram_file = await photo.get_file()

    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = os.path.join(temp_dir, "card.jpg")
        await telegram_file.download_to_drive(custom_path=image_path)

        extraction = extract_data(image_path)

        if not extraction.get("ok"):
            await update.message.reply_text(
                f"I could not extract data from this image. Error: {extraction.get('error', 'unknown')}"
            )
            return

        data = normalize_extracted_data(extraction.get("data", {}))
        await update.message.reply_text(_format_summary(data))


def build_application() -> Application:
    settings = get_settings()
    validate_settings(settings)

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(~filters.PHOTO, handle_non_photo))
    return app


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    try:
        app = build_application()
    except ConfigError as exc:
        LOGGER.error(str(exc))
        raise

    LOGGER.info("Bot started. Listening for images...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
