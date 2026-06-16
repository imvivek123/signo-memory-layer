"""LangGraph node for identifying a driver from a phone number."""

from state.agent_state import AgentState
from memory.sql_memory import create_driver, get_driver_by_phone
from utils.phone_normalization import log_phone_normalization, normalize_phone


def identify_driver(state: AgentState) -> AgentState:
    """Fetch driver data from PostgreSQL and add it to graph state."""

    print("[LangGraph] Identifying driver...")

    try:
        compressed_memory = state.get("compressed_memory") or {}
        original_phone_number = state.get("phone_number") or compressed_memory.get("phone_number", "")
        phone_number = normalize_phone(original_phone_number)
        language = compressed_memory.get("language") or "English"
        log_phone_normalization(original_phone_number, phone_number)

        if not phone_number:
            print("[LangGraph] No phone number provided.")
            return {
                "driver_data": {},
                "new_driver": False,
            }

        driver = get_driver_by_phone(phone_number)

        if driver is not None:
            print("[LangGraph] Existing driver found.")
            return {
                "driver_data": driver,
                "new_driver": False,
            }

        print("[LangGraph] New driver detected.")
        print("[LangGraph] New driver detected. Creating profile...")

        new_driver = create_driver(
            phone_number=phone_number,
            preferred_language=language,
        )

        if new_driver is None:
            print("[LangGraph] Driver profile could not be created.")
            return {
                "driver_data": {},
                "new_driver": False,
            }

        print("[LangGraph] Driver profile created successfully.")
        return {
            "driver_data": new_driver,
            "new_driver": True,
        }

    except Exception as error:
        print(f"[LangGraph] Error identifying driver: {error}")
        return {
            "driver_data": {},
            "new_driver": False,
        }
