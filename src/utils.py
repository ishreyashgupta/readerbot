import re
from typing import Any, Dict


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
JOB_TITLE_HINTS = (
    "agent",
    "analyst",
    "architect",
    "associate",
    "broker",
    "ceo",
    "cfo",
    "coo",
    "consultant",
    "coordinator",
    "cto",
    "designer",
    "developer",
    "director",
    "engineer",
    "executive",
    "founder",
    "head",
    "lead",
    "manager",
    "officer",
    "president",
    "realtor",
    "real estate",
    "representative",
    "specialist",
    "supervisor",
    "vice president",
    "vp",
)

NAME_PREFIXES = (
    "dr.",
    "dr",
    "mr.",
    "mr",
    "mrs.",
    "mrs",
    "ms.",
    "ms",
    "prof.",
    "prof",
)


def validate_email(email: str) -> bool:
    if not email:
        return False
    return bool(EMAIL_RE.match(email.strip()))


def clean_phone(phone: str) -> str:
    if not phone:
        return ""

    value = phone.strip()
    keep_plus = value.startswith("+")
    digits = re.sub(r"\D", "", value)

    if not digits:
        return ""
    if keep_plus:
        return f"+{digits}"
    return digits


def safe_get(data: Dict[str, Any], key: str, default: str = "") -> str:
    value = data.get(key, default)
    if value is None:
        return default
    return str(value).strip()


def _looks_like_job_title(value: str) -> bool:
    text = value.strip().lower()
    if not text:
        return False
    return any(token in text for token in JOB_TITLE_HINTS)


def normalize_name(name: str) -> str:
    text = safe_get({"name": name}, "name")
    if not text:
        return ""

    words = []
    for raw_word in text.replace(".", ". ").split():
        if raw_word.lower().rstrip(".") in {prefix.rstrip(".") for prefix in NAME_PREFIXES}:
            words.append(raw_word[:1].upper() + raw_word[1:].lower().rstrip(".") + ".")
            continue
        words.append(raw_word[:1].upper() + raw_word[1:].lower())

    return " ".join(words).replace(" .", ".")


def normalize_extracted_data(data: Dict[str, Any]) -> Dict[str, str]:
    designation = safe_get(data, "designation")
    company = safe_get(data, "company")

    number1 = clean_phone(safe_get(data, "number1") or safe_get(data, "phone"))
    number2 = clean_phone(safe_get(data, "number2"))
    number3 = clean_phone(safe_get(data, "number3"))
    number4 = clean_phone(safe_get(data, "number4"))

    if company and not designation and _looks_like_job_title(company):
        designation = company
        company = ""
    elif designation and company and _looks_like_job_title(company) and not _looks_like_job_title(designation):
        designation, company = company, designation

    return {
        "name": normalize_name(safe_get(data, "name")),
        "designation": designation,
        "company": company,
        "email": safe_get(data, "email").lower(),
        "phone": number1,
        "number1": number1,
        "number2": number2,
        "number3": number3,
        "number4": number4,
    }
