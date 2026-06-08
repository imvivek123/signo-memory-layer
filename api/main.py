"""FastAPI application for the Signo AI memory layer.

This API serves driver memory to an OmniDimension voice AI agent.

PostgreSQL stores structured memory: exact rows for drivers, payments, support
tickets, and call logs.

Redis stores temporary session memory: fast cached data for active or recent
conversations.

Pinecone stores semantic memory: local sentence-transformers embeddings that
let the system find old calls by meaning, not only by exact keywords.

LangGraph orchestrates the memory steps so each workflow has a clear order:
identify the driver, fetch memory, build context, and save new memory.
"""

import json

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from graphs.fetch_memory_graph import fetch_memory_graph
from graphs.save_memory_graph import save_memory_graph
from memory.session_memory import clear_session, get_session, set_session
from memory.sql_memory import (
    get_driver_by_phone,
    get_driver_payments,
    get_open_tickets,
    save_call_log,
)
from memory.vector_memory import save_memory, search_memories
from models.request_models import OmniDimensionWebhookPayload
from utils.memory_extractor import extract_memory


# Create the FastAPI app object.
# Uvicorn uses this variable when running: uvicorn api.main:app --reload
app = FastAPI(
    title="Signo Memory Layer API",
    description="Backend memory layer for Signo's OmniDimension voice AI agent.",
    version="0.1.0",
)


class CallLogRequest(BaseModel):
    """Request body for saving one completed voice call.

    OmniDimension or another service can send this JSON after a call ends.
    """

    phone_number: str = Field(
        ...,
        description="Driver phone number used during the call.",
    )
    call_summary: str = Field(
        ...,
        description="Short summary of the call.",
    )
    call_transcript: str | None = Field(
        default=None,
        description="Full transcript of the call, if available.",
    )
    intent: str | None = Field(
        default=None,
        description="Main reason for the call, such as payment_issue.",
    )
    sentiment: str | None = Field(
        default=None,
        description="Simple call sentiment, such as positive, neutral, or negative.",
    )
    follow_up_required: bool = Field(
        default=False,
        description="True if the Signo team should follow up after this call.",
    )
    is_resolved: bool = Field(
        default=False,
        description="True if the conversation was fully resolved during the call.",
    )


@app.get("/")
def root():
    """Health-check endpoint.

    Open this URL in a browser to confirm that the API server is running.
    """

    return {
        "message": "Signo Memory Layer API is running",
        "status": "ok",
    }


@app.get("/driver/{phone_number}")
def get_driver_memory(phone_number: str):
    """Return driver memory for one phone number.

    The voice AI agent can call this endpoint when it knows a driver's phone
    number and needs useful context for the conversation.

    Architecture:
    1. Redis is checked first because it is very fast temporary session memory.
    2. PostgreSQL is used when Redis does not already have the data.
    3. Fresh PostgreSQL data is saved back into Redis for the next request.
    """

    print("Fetching from Redis cache...")
    cached_driver_memory = get_session(phone_number)

    if cached_driver_memory is not None:
        return {
            "source": "redis_cache",
            **cached_driver_memory,
        }

    print("Fetching from PostgreSQL...")
    driver = get_driver_by_phone(phone_number)

    if driver is None:
        raise HTTPException(
            status_code=404,
            detail="Driver not found for the provided phone number.",
        )

    driver_id = driver["driver_id"]

    # Fetch related memory after the driver exists.
    # Payments and tickets are kept as separate lists in the JSON response
    # so the caller can decide how to use each type of information.
    payments = get_driver_payments(driver_id)
    open_tickets = get_open_tickets(driver_id)

    response_data = {
        "driver": driver,
        "payments": payments,
        "open_tickets": open_tickets,
    }

    print("Saving response to Redis...")
    set_session(phone_number, response_data)

    return {
        "source": "postgresql",
        **response_data,
    }


@app.post("/call-log")
def create_call_log(call_log: CallLogRequest):
    """Store memory from a completed voice AI call.

    This is the endpoint to call after OmniDimension finishes a conversation.
    Resolved conversations are intentionally skipped so the database stores
    only call memory that may be needed later.

    The call is saved twice:
    1. PostgreSQL keeps the structured record.
    2. Pinecone keeps a semantic vector so similar future issues can be found.
    """

    # If the issue was fully resolved in the call, do not store it.
    # This keeps PostgreSQL focused on unresolved or useful future memory.
    if call_log.is_resolved:
        return {
            "message": "Conversation was resolved, so it was not stored.",
            "stored": False,
        }

    driver = get_driver_by_phone(call_log.phone_number)

    if driver is None:
        raise HTTPException(
            status_code=404,
            detail="Cannot save call log because the driver was not found.",
        )

    saved_call_log = save_call_log(
        driver_id=driver["driver_id"],
        compressed_memory={
            "phone_number": call_log.phone_number,
            "driver_id": driver["driver_id"],
            "language": "",
            "issue_category": call_log.intent or "",
            "issue_summary": "",
            "conversation_summary": "",
            "call_summary": call_log.call_summary,
            "sentiment": call_log.sentiment or "",
            "important": bool(call_log.follow_up_required),
            "follow_up_required": call_log.follow_up_required,
        },
    )

    if saved_call_log is None:
        raise HTTPException(
            status_code=500,
            detail="Call log could not be saved.",
        )

    semantic_memory = save_memory(
        phone_number=call_log.phone_number,
        text=f"""
Issue:

Conversation:

Summary:
{call_log.call_summary}
""".strip(),
        metadata={
            "phone_number": call_log.phone_number,
            "driver_id": driver["driver_id"],
            "issue_category": call_log.intent or "",
            "sentiment": call_log.sentiment or "",
            "important": bool(call_log.follow_up_required),
            "timestamp": saved_call_log.get("created_at"),
        },
    )
    clear_session(call_log.phone_number)

    return {
        "message": "Call log saved successfully",
        "call_log": saved_call_log,
        "semantic_memory_saved": semantic_memory is not None,
        "semantic_memory": semantic_memory,
    }


@app.get("/semantic-memory/{phone_number}")
def get_semantic_memory(
    phone_number: str,
    query: str = Query(
        ...,
        description="Natural-language search query, such as payment issue.",
    ),
):
    """Return the top semantic memories for a driver.

    Example:
    A driver says, "My payment problem happened again."
    Semantic search can retrieve, "Driver previously complained about delayed
    payment last week," even though the wording is different.
    """

    matches = search_memories(phone_number=phone_number, query=query)

    return {
        "phone_number": phone_number,
        "query": query,
        "matches": matches,
    }


@app.get("/memory/context/{phone_number}")
def get_memory_context(
    phone_number: str,
    query: str | None = Query(
        default=None,
        description="Optional current issue summary used for semantic search.",
    ),
):
    """Run the LangGraph during-call memory retrieval workflow."""

    initial_state = {
        "phone_number": phone_number,
        "driver_data": {},
        "payments": [],
        "tickets": [],
        "semantic_memories": [],
        "call_summary": query or "",
        "intent": "",
        "sentiment": "",
        "final_context": "",
        "memory_saved": False,
        "new_driver": False,
    }

    final_state = fetch_memory_graph.invoke(initial_state)

    return {
        "phone_number": phone_number,
        "context": final_state.get("final_context", ""),
        "semantic_memories": final_state.get("semantic_memories", []),
    }


@app.post("/memory/save")
def save_memory_with_graph(payload: OmniDimensionWebhookPayload):
    """Run the LangGraph after-call memory saving workflow.

    This endpoint accepts the full OmniDimension webhook payload directly.
    """

    print("[OmniDimension] Webhook received")
    payload_dict = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()

    print("=" * 80)
    print("RAW OMNIDIMENSION WEBHOOK PAYLOAD")
    print(json.dumps(payload_dict, indent=2, default=str))
    print("=" * 80)

    compressed_memory = extract_memory(payload_dict)
    print(f"[MemoryExtractor] Compressed memory: {compressed_memory}")
    print("[DEBUG] Extracted phone_number:", compressed_memory.get("phone_number"))
    print("[DEBUG] Extracted driver_id:", compressed_memory.get("driver_id"))

    phone_number = compressed_memory["phone_number"]

    if not phone_number:
        return {
            "message": "Webhook received successfully",
            "warning": "phone_number missing",
            "compressed_memory": compressed_memory,
            "raw_payload": payload_dict,
        }

    initial_state = {
        "compressed_memory": compressed_memory,
        "driver_data": {},
        "memory_saved": False,
        "new_driver": False,
    }

    print("[LangGraph] Saving compressed conversational memory...")
    final_state = save_memory_graph.invoke(initial_state)
    memory_saved = final_state.get("memory_saved", False)

    if not memory_saved:
        raise HTTPException(
            status_code=500,
            detail="Memory could not be saved by the LangGraph workflow.",
        )

    return {
        "message": "Memory saved",
        "memory_saved": memory_saved,
        "phone_number": phone_number,
        "compressed_memory": compressed_memory,
    }
