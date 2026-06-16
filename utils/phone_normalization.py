"""Shared phone number normalization helpers."""


def normalize_phone(phone_number: str) -> str:
    """Normalize phone numbers for consistent storage and lookup."""

    if not phone_number:
        return ""

    return str(phone_number).replace("+", "").strip()


def log_phone_normalization(phone_number: str, normalized_phone: str) -> None:
    """Log original and normalized phone values for debugging."""

    print(f"[PhoneNormalization] Original: {phone_number}")
    print(f"[PhoneNormalization] Normalized: {normalized_phone}")
