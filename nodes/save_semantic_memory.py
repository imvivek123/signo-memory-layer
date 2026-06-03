"""LangGraph node for saving call memory into Pinecone."""

from state.agent_state import AgentState
from memory.session_memory import clear_session
from memory.vector_memory import save_memory


def save_semantic_memory(state: AgentState) -> AgentState:
    """Save a completed call summary as semantic vector memory."""

    print("[LangGraph] Saving semantic memory...")

    try:
        if not state.get("memory_saved"):
            print("[LangGraph] Semantic save skipped because PostgreSQL save failed.")
            return {"memory_saved": False}

        compressed_memory = state.get("compressed_memory") or {}
        saved_call_log = state.get("saved_call_log") or {}
        driver_data = state.get("driver_data") or {}

        phone_number = compressed_memory.get("phone_number", "")
        call_summary = compressed_memory.get("call_summary", "")
        issue_summary = compressed_memory.get("issue_summary", "")
        conversation_summary = compressed_memory.get("conversation_summary", "")
        issue_category = compressed_memory.get("issue_category", "")

        if not phone_number or not call_summary:
            print("[LangGraph] Semantic save skipped because required data is missing.")
            return {"memory_saved": False}

        # Only clean conversational text is embedded. Raw interactions, bot
        # prompts, recordings, and webhook metadata add noise to vector search.
        semantic_text = f"""
Issue: {issue_summary}

Conversation:
{conversation_summary}

Summary:
{call_summary}
""".strip()

        semantic_memory = save_memory(
            phone_number=phone_number,
            text=semantic_text,
            metadata={
                "phone_number": phone_number,
                "driver_id": compressed_memory.get("driver_id") or driver_data.get("driver_id", ""),
                "issue_category": issue_category,
                "sentiment": compressed_memory.get("sentiment", ""),
                "important": compressed_memory.get("important", False),
                "timestamp": saved_call_log.get("created_at", ""),
            },
        )

        if semantic_memory is None:
            print("[LangGraph] Semantic memory was not saved.")
            return {"memory_saved": False}

        print("[Pinecone] Semantic conversational memory saved.")

        if clear_session(phone_number):
            print("[Redis] Driver cache invalidated.")
        else:
            print("[Redis] Driver cache invalidation skipped or failed.")

        return {"memory_saved": True}

    except Exception as error:
        print(f"[LangGraph] Error saving semantic memory: {error}")
        return {"memory_saved": False}
