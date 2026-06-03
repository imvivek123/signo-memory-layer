"""Manual test for the LangGraph memory retrieval flow.

Run from the project root:

    python tests/test_fetch_graph.py
"""

import os
import sys
from pprint import pprint


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from graphs.fetch_memory_graph import fetch_memory_graph


if __name__ == "__main__":
    initial_state = {
        "phone_number": "+919876543210",
        "call_summary": "Driver says the payment problem happened again.",
        "driver_data": {},
        "payments": [],
        "tickets": [],
        "semantic_memories": [],
        "final_context": "",
        "memory_saved": False,
        "new_driver": False,
    }

    final_state = fetch_memory_graph.invoke(initial_state)

    print("\nFinal fetch graph state:")
    pprint(final_state)
