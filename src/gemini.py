import json
import logging
import mimetypes
import os
import base64
from typing import Any, Dict
from urllib import error, request

from src.config import get_settings
from src.utils import normalize_extracted_data


LOGGER = logging.getLogger(__name__)

_PROMPT = (
    "Extract name, designation, company, email, and up to 4 phone numbers from this business card. "
    "Designation means job title (for example: Manager, Realtor, Engineer). "
    "Company means organization/business name (for example: ABC Realty, Google). "
    "If the card only shows a title and no company name, keep company as an empty string. "
    "Return only valid JSON with keys: name, designation, company, email, number1, number2, number3, number4. "
    "If only one phone number is found, set it in number1 and keep number2-number4 empty."
)


def _strip_fenced_json(text: str) -> str:
    value = text.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return value


def _extract_json_dict(raw_text: str) -> Dict[str, Any]:
    cleaned = _strip_fenced_json(raw_text)
    return json.loads(cleaned)


def _read_image_payload(image_path: str) -> Dict[str, str]:
    settings = get_settings()

    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

    mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return {
        "imageBase64": encoded,
        "mimeType": mime_type,
        "fileName": os.path.basename(image_path),
        "prompt": _PROMPT,
        "emailSubject": settings.email_subject,
        "emailBody": settings.email_body,
    }


def _extract_data_candidate(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    if isinstance(payload.get("data"), dict):
        return payload["data"]
    if isinstance(payload.get("result"), dict):
        return payload["result"]
    if isinstance(payload.get("extractedData"), dict):
        return payload["extractedData"]

    # Some endpoints may return the fields at the top level.
    return payload


def _is_success(payload: Dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    ok_value = payload.get("ok")
    if isinstance(ok_value, bool):
        return ok_value
    if isinstance(ok_value, str):
        return ok_value.strip().lower() == "true"
    return True


def extract_data(image_path: str) -> Dict[str, Any]:
    settings = get_settings()

    try:
        payload = _read_image_payload(image_path)
        body = json.dumps(payload).encode("utf-8")

        req = request.Request(
            settings.apps_script_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with request.urlopen(req, timeout=60) as response:
            raw_text = response.read().decode("utf-8", errors="replace")

        parsed = _extract_json_dict(raw_text)
        if not _is_success(parsed):
            return {
                "ok": False,
                "data": {
                    "name": "",
                    "designation": "",
                    "company": "",
                    "email": "",
                    "phone": "",
                    "number1": "",
                    "number2": "",
                    "number3": "",
                    "number4": "",
                },
                "error": str(parsed.get("error", "Apps Script returned failure")),
                "raw": raw_text,
            }

        normalized = normalize_extracted_data(_extract_data_candidate(parsed))
        return {
            "ok": True,
            "data": normalized,
            "error": "",
            "raw": raw_text,
        }
    except json.JSONDecodeError as exc:
        LOGGER.warning("Apps Script returned non-JSON content")
        return {
            "ok": False,
            "data": {
                "name": "",
                "designation": "",
                "company": "",
                "email": "",
                "phone": "",
                "number1": "",
                "number2": "",
                "number3": "",
                "number4": "",
            },
            "error": f"Invalid JSON from Apps Script: {exc}",
            "raw": raw_text if "raw_text" in locals() else "",
        }
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else ""
        LOGGER.exception("Apps Script HTTP error")
        return {
            "ok": False,
            "data": {
                "name": "",
                "designation": "",
                "company": "",
                "email": "",
                "phone": "",
                "number1": "",
                "number2": "",
                "number3": "",
                "number4": "",
            },
            "error": f"HTTP {exc.code}: {details or str(exc)}",
            "raw": details,
        }
    except Exception as exc:  # pragma: no cover - network behavior
        LOGGER.exception("Apps Script extraction failed")
        return {
            "ok": False,
            "data": {
                "name": "",
                "designation": "",
                "company": "",
                "email": "",
                "phone": "",
                "number1": "",
                "number2": "",
                "number3": "",
                "number4": "",
            },
            "error": str(exc),
            "raw": "",
        }
