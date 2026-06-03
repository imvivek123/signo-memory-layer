"""LangGraph node for fetching semantic Pinecone memory."""

from state.agent_state import AgentState
from memory.vector_memory import search_memories


def fetch_semantic_memory(state: AgentState) -> AgentState:
    """Search Pinecone for semantically similar past memories."""

    print("[LangGraph] Fetching semantic memory...")

    try:
        phone_number = state.get("phone_number", "")
        search_query = state.get("call_summary") or "driver issues"

        if not phone_number:
            print("[LangGraph] Semantic memory skipped because phone number is missing.")
            return {"semantic_memories": []}

        semantic_memories = search_memories(
            phone_number=phone_number,
            query=search_query,
        )

        print("[LangGraph] Semantic memories retrieved.")
        return {"semantic_memories": semantic_memories}

    except Exception as error:
        print(f"[LangGraph] Error fetching semantic memory: {error}")
        return {"semantic_memories": []}
