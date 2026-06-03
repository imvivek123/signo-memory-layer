"""Production-style memory extraction for OmniDimension webhook payloads.

The webhook can contain call metadata, bot messages, recordings, sequence data,
and other details that are not useful long-term memory. This module compresses
the payload into only the information Signo should remember.
"""

from typing import Any


NEGATIVE_KEYWORDS = [
    "delay",
    "payment",
    "harassment",
    "police",
    "rto",
    "emergency",
    "frustrated",
    "complaint",
    "problem",
    "issue",
]

IMPORTANT_CATEGORIES = [
    "Route issue",
    "Payment issue",
    "Emergency",
    "Complaint",
    "Harassment",
]


def _safe_get(data: dict[str, Any], *keys: str, default: Any = "") -> Any:
    """Safely read nested dictionary values.

    Webhook payloads can be incomplete during testing or failures. This helper
    prevents KeyError and returns a clean default instead.
    """

    current = data

    for key in keys:
        if not isinstance(current, dict):
            return default

        current = current.get(key)

        if current is None:
            return default

    return current


def _normalize_text(value: Any) -> str:
    """Convert optional webhook values into safe strings."""

    if value is None:
        return ""

    return str(value).strip()


def _detect_sentiment(*texts: str) -> str:
    """Detect simple negative/neutral sentiment from business keywords."""

    searchable_text = " ".join(texts).lower()

    for keyword in NEGATIVE_KEYWORDS:
        if keyword.lower() in searchable_text:
            return "negative"

    return "neutral"


def _is_important(issue_category: str, sentiment: str) -> bool:
    """Decide whether this call should be remembered as important."""

    normalized_category = issue_category.strip().lower()
    important_categories = {
        category.strip().lower()
        for category in IMPORTANT_CATEGORIES
    }

    return normalized_category in important_categories or sentiment == "negative"


def _needs_follow_up(issue_category: str, sentiment: str) -> bool:
    """Decide if the Signo team should follow up after the call."""

    normalized_category = issue_category.strip().lower()

    if sentiment == "negative":
        return True

    if normalized_category == "emergency":
        return True

    if "harassment" in normalized_category:
        return True

    return False


def extract_memory(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract only important conversational memory from a full webhook.

    Args:
        payload: Full OmniDimension webhook payload as a normal dictionary.

    Returns:
        A compressed memory object with only business-relevant fields.
    """

    print("[MemoryExtractor] Processing OmniDimension payload...")
    print("[MemoryExtractor] Extracting important memory...")

    extracted_variables = _safe_get(
        payload,
        "call_report",
        "extracted_variables",
        default={},
    )

    phone_number = _normalize_text(
        _safe_get(extracted_variables, "driver_mobile_number")
    )
    driver_id = _normalize_text(
        _safe_get(extracted_variables, "driver_id")
    )
    language = _normalize_text(
        _safe_get(extracted_variables, "language")
    )
    issue_category = _normalize_text(
        _safe_get(extracted_variables, "category_selected")
    )
    issue_summary = _normalize_text(
        _safe_get(extracted_variables, "query_description")
    )
    conversation_summary = _normalize_text(
        _safe_get(extracted_variables, "conversation_summary")
    )
    call_summary = _normalize_text(
        _safe_get(payload, "call_report", "summary")
    )

    sentiment = _detect_sentiment(
        issue_summary,
        conversation_summary,
        call_summary,
    )
    important = _is_important(issue_category, sentiment)
    follow_up_required = _needs_follow_up(issue_category, sentiment)

    compressed_memory = {
        "phone_number": phone_number,
        "driver_id": driver_id,
        "language": language,
        "issue_category": issue_category,
        "issue_summary": issue_summary,
        "conversation_summary": conversation_summary,
        "call_summary": call_summary,
        "sentiment": sentiment,
        "important": important,
        "follow_up_required": follow_up_required,
    }

    print("[MemoryExtractor] Compressed memory object created.")
    return compressed_memory
