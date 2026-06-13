"""LangGraph node for saving call memory into Pinecone - WITH EXTENSIVE DEBUG LOGS."""

import traceback
from state.agent_state import AgentState
from memory.session_memory import clear_session
from memory.vector_memory import save_memory


def save_semantic_memory(state: AgentState) -> AgentState:
    """Save a completed call summary as semantic vector memory."""

    print("\n" + "="*80)
    print("[DEBUG-SEMANTIC] ENTERING save_semantic_memory()")
    print("="*80)

    try:
        # Check memory_saved flag
        memory_saved_flag = state.get("memory_saved")
        print(f"[DEBUG-SEMANTIC] state['memory_saved'] = {memory_saved_flag}")
        print(f"[DEBUG-SEMANTIC] memory_saved_flag type: {type(memory_saved_flag)}")

        if not memory_saved_flag:
            print("[DEBUG-SEMANTIC] ⚠️ CHECKPOINT: PostgreSQL save was not successful")
            print("[DEBUG-SEMANTIC] Semantic save SKIPPED because memory_saved=False")
            return {"memory_saved": False}

        # Extract compressed memory
        compressed_memory = state.get("compressed_memory") or {}
        print(f"[DEBUG-SEMANTIC] Extracted compressed_memory (keys): {list(compressed_memory.keys())}")

        saved_call_log = state.get("saved_call_log") or {}
        print(f"[DEBUG-SEMANTIC] Extracted saved_call_log (keys): {list(saved_call_log.keys())}")

        driver_data = state.get("driver_data") or {}
        print(f"[DEBUG-SEMANTIC] Extracted driver_data (keys): {list(driver_data.keys())}")

        # Extract individual fields
        phone_number = compressed_memory.get("phone_number", "")
        call_summary = compressed_memory.get("call_summary", "")
        issue_summary = compressed_memory.get("issue_summary", "")
        conversation_summary = compressed_memory.get("conversation_summary", "")
        issue_category = compressed_memory.get("issue_category", "")

        print(f"[DEBUG-SEMANTIC] phone_number: '{phone_number}' (len={len(phone_number)})")
        print(f"[DEBUG-SEMANTIC] call_summary: '{call_summary[:100]}...' (len={len(call_summary)})")
        print(f"[DEBUG-SEMANTIC] issue_summary: '{issue_summary}' (len={len(issue_summary)})")
        print(f"[DEBUG-SEMANTIC] conversation_summary: '{conversation_summary[:100]}...' (len={len(conversation_summary)})")
        print(f"[DEBUG-SEMANTIC] issue_category: '{issue_category}'")

        # Validate required fields
        if not phone_number or not call_summary:
            print("[DEBUG-SEMANTIC] ⚠️ CHECKPOINT: Required data is missing")
            print(f"[DEBUG-SEMANTIC] phone_number present: {bool(phone_number)}")
            print(f"[DEBUG-SEMANTIC] call_summary present: {bool(call_summary)}")
            print("[DEBUG-SEMANTIC] Semantic save SKIPPED")
            return {"memory_saved": False}

        # Construct semantic text
        semantic_text = f"""
Issue: {issue_summary}

Conversation:
{conversation_summary}

Summary:
{call_summary}
""".strip()

        print(f"[DEBUG-SEMANTIC] ✓ semantic_text constructed (len={len(semantic_text)})")
        print(f"[DEBUG-SEMANTIC] semantic_text FIRST 200 CHARS:\n{semantic_text[:200]}")
        print(f"[DEBUG-SEMANTIC] semantic_text LAST 200 CHARS:\n{semantic_text[-200:]}")

        # Build metadata
        driver_id = compressed_memory.get("driver_id") or driver_data.get("driver_id", "")
        metadata_dict = {
            "phone_number": phone_number,
            "driver_id": driver_id,
            "issue_category": issue_category,
            "sentiment": compressed_memory.get("sentiment", ""),
            "important": compressed_memory.get("important", False),
            "timestamp": saved_call_log.get("created_at", ""),
        }
        print(f"[DEBUG-SEMANTIC] metadata constructed: {metadata_dict}")

        # CRITICAL: Call save_memory()
        print(f"[DEBUG-SEMANTIC] 🔄 CALLING save_memory()")
        print(f"[DEBUG-SEMANTIC]   - phone_number='{phone_number}'")
        print(f"[DEBUG-SEMANTIC]   - text length={len(semantic_text)}")
        print(f"[DEBUG-SEMANTIC]   - metadata keys={list(metadata_dict.keys())}")

        semantic_memory = save_memory(
            phone_number=phone_number,
            text=semantic_text,
            metadata=metadata_dict,
        )

        print(f"[DEBUG-SEMANTIC] ✓ save_memory() returned")
        print(f"[DEBUG-SEMANTIC] semantic_memory result: {semantic_memory}")

        if semantic_memory is None:
            print("[DEBUG-SEMANTIC] ⚠️ CHECKPOINT: save_memory() returned None")
            print("[DEBUG-SEMANTIC] Semantic memory was NOT saved to Pinecone")
            return {"memory_saved": False}

        print(f"[DEBUG-SEMANTIC] ✓ semantic_memory saved successfully")
        print(f"[DEBUG-SEMANTIC] semantic_memory['id']: {semantic_memory.get('id')}")

        # Try to clear cache
        print(f"[DEBUG-SEMANTIC] 🔄 Attempting to clear session cache for {phone_number}")

        if clear_session(phone_number):
            print("[DEBUG-SEMANTIC] ✓ Redis cache invalidated successfully")
        else:
            print("[DEBUG-SEMANTIC] ⚠️ Redis cache invalidation failed or skipped")

        print("[DEBUG-SEMANTIC] ✓ SEMANTIC MEMORY PIPELINE COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")

        return {"memory_saved": True}

    except Exception as error:
        print("\n" + "="*80)
        print("[DEBUG-SEMANTIC] ❌ EXCEPTION IN save_semantic_memory()")
        print("="*80)
        print(f"[DEBUG-SEMANTIC] Exception type: {type(error).__name__}")
        print(f"[DEBUG-SEMANTIC] Exception message: {str(error)}")
        print("[DEBUG-SEMANTIC] Full traceback:")
        traceback.print_exc()
        print("="*80 + "\n")
        return {"memory_saved": False}
