"""LangGraph node for fetching structured PostgreSQL memory."""

from state.agent_state import AgentState
from memory.sql_memory import get_driver_payments, get_open_tickets, get_recent_call_logs
from utils.phone_normalization import log_phone_normalization, normalize_phone


def fetch_structured_memory(state: AgentState) -> AgentState:
    """Fetch PostgreSQL memory for the current driver."""

    print("[LangGraph] Fetching structured memory...")

    try:
        original_phone_number = state.get("phone_number", "")
        phone_number = normalize_phone(original_phone_number)
        driver_data = state.get("driver_data") or {}
        driver_id = driver_data.get("driver_id")

        print(f"[LangGraph] Phone number received for structured memory: {phone_number}")
        log_phone_normalization(original_phone_number, phone_number)

        recent_calls = get_recent_call_logs(phone_number) if phone_number else []
        print(f"[LangGraph] Recent call logs fetched: {len(recent_calls)}")

        if driver_id is None:
            print("[LangGraph] Structured memory skipped because driver_id is missing.")
            return {
                "payments": [],
                "tickets": [],
                "recent_calls": recent_calls,
            }

        payments = get_driver_payments(driver_id)
        tickets = get_open_tickets(driver_id)

        print("[LangGraph] Structured memory retrieved.")
        return {
            "payments": payments,
            "tickets": tickets,
            "recent_calls": recent_calls,
        }

    except Exception as error:
        print(f"[LangGraph] Error fetching structured memory: {error}")
        return {
            "payments": [],
            "tickets": [],
            "recent_calls": [],
        }
