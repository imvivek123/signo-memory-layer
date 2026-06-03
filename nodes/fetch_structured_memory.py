"""LangGraph node for fetching structured PostgreSQL memory."""

from state.agent_state import AgentState
from memory.sql_memory import get_driver_payments, get_open_tickets


def fetch_structured_memory(state: AgentState) -> AgentState:
    """Fetch payments and open support tickets for the current driver."""

    print("[LangGraph] Fetching structured memory...")

    try:
        driver_data = state.get("driver_data") or {}
        driver_id = driver_data.get("driver_id")

        if driver_id is None:
            print("[LangGraph] Structured memory skipped because driver_id is missing.")
            return {
                "payments": [],
                "tickets": [],
            }

        payments = get_driver_payments(driver_id)
        tickets = get_open_tickets(driver_id)

        print("[LangGraph] Structured memory retrieved.")
        return {
            "payments": payments,
            "tickets": tickets,
        }

    except Exception as error:
        print(f"[LangGraph] Error fetching structured memory: {error}")
        return {
            "payments": [],
            "tickets": [],
        }
