"""Manual test for the full compressed memory pipeline.

Run from the project root:

    python tests/test_full_memory_pipeline.py
"""

import os
import sys
from pprint import pprint


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from graphs.fetch_memory_graph import fetch_memory_graph
from graphs.save_memory_graph import save_memory_graph


def main():
    """Save compressed memory and fetch the resulting context."""

    compressed_memory = {
        "phone_number": "+919876543210",
        "driver_id": "omni_driver_pipeline_test",
        "language": "Hindi",
        "issue_category": "Payment issue",
        "issue_summary": "Driver says payment has not arrived again.",
        "conversation_summary": "Driver was frustrated about repeated delayed payment.",
        "call_summary": "Driver reported that the payment problem happened again.",
        "sentiment": "negative",
        "important": True,
        "follow_up_required": True,
    }

    print("\n[Pipeline Test] Sending sample compressed memory:")
    pprint(compressed_memory)

    save_state = {
        "compressed_memory": compressed_memory,
        "driver_data": {},
        "memory_saved": False,
        "new_driver": False,
    }

    print("\n[Pipeline Test] Saving to PostgreSQL and Pinecone...")
    saved_state = save_memory_graph.invoke(save_state)

    print("\n[Pipeline Test] Save graph result:")
    pprint(saved_state)

    print("\n[Pipeline Test] Fetching memory context back...")
    fetch_state = {
        "phone_number": compressed_memory["phone_number"],
        "driver_data": {},
        "payments": [],
        "tickets": [],
        "semantic_memories": [],
        "call_summary": "payment problem happened again",
        "final_context": "",
        "memory_saved": False,
        "new_driver": False,
    }

    fetched_state = fetch_memory_graph.invoke(fetch_state)

    print("\n[Pipeline Test] Retrieved semantic memories:")
    pprint(fetched_state.get("semantic_memories", []))

    print("\n[Pipeline Test] Retrieved context:")
    print(fetched_state.get("final_context", ""))


if __name__ == "__main__":
    main()
