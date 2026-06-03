"""Manual test for the LangGraph memory saving flow.

Run from the project root:

    python tests/test_save_graph.py
"""

import os
import sys
from pprint import pprint


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from graphs.save_memory_graph import save_memory_graph
from memory.sql_memory import get_driver_by_phone


def run_save_graph_test(initial_state):
    """Run the save graph and print beginner-friendly verification output."""

    compressed_memory = initial_state["compressed_memory"]

    print("\nRunning save graph test for:", compressed_memory["phone_number"])
    final_state = save_memory_graph.invoke(initial_state)

    print("\nFinal save graph state:")
    pprint(final_state)

    driver = get_driver_by_phone(compressed_memory["phone_number"])

    print("\nVerification:")
    print(f"New driver row exists? {driver is not None}")
    print(f"Call log and semantic memory saved? {final_state.get('memory_saved')}")

    return final_state


if __name__ == "__main__":
    initial_state = {
        "compressed_memory": {
            "phone_number": "+919876543210",
            "driver_id": "omni_existing_driver",
            "language": "Hindi",
            "issue_category": "payment_issue",
            "issue_summary": "Driver complained about delayed payment.",
            "conversation_summary": "Driver said delayed payment happened again.",
            "call_summary": "Driver complained that delayed payment happened again.",
            "sentiment": "negative",
            "important": True,
            "follow_up_required": True,
        },
        "driver_data": {},
        "memory_saved": False,
        "new_driver": False,
    }

    new_driver_state = {
        "compressed_memory": {
            "phone_number": "+919999999999",
            "driver_id": "omni_new_driver",
            "language": "English",
            "issue_category": "payment_issue",
            "issue_summary": "New driver reported a delayed payment issue.",
            "conversation_summary": "New driver needs follow-up for delayed payment.",
            "call_summary": "New driver reported a delayed payment issue.",
            "sentiment": "negative",
            "important": True,
            "follow_up_required": True,
        },
        "driver_data": {},
        "memory_saved": False,
        "new_driver": False,
    }

    run_save_graph_test(initial_state)
    run_save_graph_test(new_driver_state)
