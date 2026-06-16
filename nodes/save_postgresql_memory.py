"""LangGraph node for saving call memory into PostgreSQL."""

from state.agent_state import AgentState
from memory.sql_memory import create_driver, get_driver_by_phone, save_call_log
from utils.phone_normalization import log_phone_normalization, normalize_phone


def save_postgresql_memory(state: AgentState) -> AgentState:
    """Save compressed conversational memory into PostgreSQL."""

    print("[LangGraph] Saving PostgreSQL memory...")

    try:
        compressed_memory = state.get("compressed_memory") or {}
        original_phone_number = compressed_memory.get("phone_number", "")
        phone_number = normalize_phone(original_phone_number)
        compressed_memory = {
            **compressed_memory,
            "phone_number": phone_number,
        }
        call_summary = compressed_memory.get("call_summary", "")
        log_phone_normalization(original_phone_number, phone_number)

        if not phone_number or not call_summary:
            print("[LangGraph] PostgreSQL save skipped because required data is missing.")
            return {"memory_saved": False}

        driver_data = state.get("driver_data") or get_driver_by_phone(phone_number)
        created_driver_in_node = False

        if not driver_data:
            print("[LangGraph] New driver detected.")
            print("[LangGraph] New driver detected. Creating profile...")
            driver_data = create_driver(phone_number=phone_number)

            if not driver_data:
                print("[LangGraph] PostgreSQL save failed because driver was not found.")
                return {
                    "driver_data": {},
                    "memory_saved": False,
                    "new_driver": False,
                }

            print("[LangGraph] Driver profile created successfully.")
            created_driver_in_node = True

        saved_call_log = save_call_log(
            driver_id=driver_data["driver_id"],
            compressed_memory=compressed_memory,
        )

        if saved_call_log is None:
            print("[LangGraph] PostgreSQL memory was not saved.")
            return {
                "driver_data": driver_data,
                "memory_saved": False,
            }

        print("[LangGraph] PostgreSQL memory saved.")
        return {
            "driver_data": driver_data,
            "phone_number": phone_number,
            "saved_call_log": saved_call_log,
            "memory_saved": True,
            "new_driver": state.get("new_driver", False) or created_driver_in_node,
        }

    except Exception as error:
        print(f"[LangGraph] Error saving PostgreSQL memory: {error}")
        return {"memory_saved": False}
