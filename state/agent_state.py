"""Shared state definition for Signo LangGraph workflows."""

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """Data shared between LangGraph nodes.

    LangGraph passes one state dictionary through the workflow. Each node reads
    the fields it needs, does one focused job, and returns only the fields it
    wants to update. LangGraph merges those returned values back into the
    shared state for the next node.
    """

    phone_number: str
    compressed_memory: dict
    driver_data: dict
    payments: list
    tickets: list
    recent_calls: list
    semantic_memories: list
    call_summary: str
    intent: str
    sentiment: str
    issue_category: str
    issue_summary: str
    important: bool
    final_context: str
    memory_saved: bool
    new_driver: bool
    conversation_summary: str
    language: str
