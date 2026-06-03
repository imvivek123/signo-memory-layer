"""Manual test for the OmniDimension memory extractor.

Run from the project root:

    python tests/test_memory_extractor.py
"""

import os
import sys
from pprint import pprint


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.memory_extractor import extract_memory


if __name__ == "__main__":
    omnidimension_payload = {
        "call_id": "call_123",
        "bot_id": "bot_456",
        "bot_name": "Signo Driver Support",
        "call_status": "completed",
        "recording_url": "https://example.com/recording.mp3",
        "sequence_data": {"step": 3},
        "call_report": {
            "summary": "Driver reported that payment is delayed again.",
            "extracted_variables": {
                "driver_mobile_number": "+919999999999",
                "driver_id": "omni_driver_789",
                "language": "English",
                "category_selected": "Payment issue",
                "query_description": "Payment has not arrived yet.",
                "conversation_summary": "Driver was frustrated about delayed payment.",
                "menu_selection": "2",
            },
            "interactions": [
                {
                    "role": "driver",
                    "message": "My payment problem happened again.",
                },
                {
                    "role": "agent",
                    "message": "I will save this issue for follow-up.",
                },
            ],
        },
    }

    compressed_memory = extract_memory(omnidimension_payload)

    print("\nCompressed memory object:")
    pprint(compressed_memory)

    unwanted_fields = [
        "interactions",
        "recording_url",
        "bot_id",
        "bot_name",
        "call_status",
        "sequence_data",
        "menu_selection",
    ]

    leaked_fields = [
        field
        for field in unwanted_fields
        if field in compressed_memory
    ]

    print("\nUnwanted fields removed?", not leaked_fields)

    if leaked_fields:
        print("Fields that should not be present:")
        pprint(leaked_fields)
