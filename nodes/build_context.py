"""LangGraph node for building one AI-ready memory context string."""

from state.agent_state import AgentState


def _format_key_values(title: str, data: dict) -> str:
    """Format a dictionary as readable lines for an LLM."""

    if not data:
        return f"{title}: Not found"

    lines = [f"{title}:"]

    for key, value in data.items():
        label = key.replace("_", " ").title()
        lines.append(f"- {label}: {value}")

    return "\n".join(lines)


def _format_list(title: str, items: list) -> str:
    """Format a list of dictionaries as readable bullet points."""

    if not items:
        return f"{title}:\n- None"

    lines = [f"{title}:"]

    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            details = ", ".join(
                f"{key.replace('_', ' ').title()}: {value}"
                for key, value in item.items()
            )
            lines.append(f"- {index}. {details}")
        else:
            lines.append(f"- {index}. {item}")

    return "\n".join(lines)


def _format_semantic_memories(memories: list) -> str:
    """Format semantic matches from Pinecone into LLM-friendly text."""

    if not memories:
        return "Past Semantic Memories:\n- None"

    lines = ["Past Semantic Memories:"]

    for index, memory in enumerate(memories, start=1):
        metadata = memory.get("metadata", {}) if isinstance(memory, dict) else {}
        driver_id = metadata.get("driver_id", "")
        issue_category = metadata.get("issue_category", "")
        sentiment = metadata.get("sentiment", "")
        important = metadata.get("important", False)
        score = memory.get("score") if isinstance(memory, dict) else None

        line = f"- {index}. Issue Category: {issue_category or 'Unknown'}"

        if driver_id:
            line += f" | Driver Id: {driver_id}"

        if sentiment:
            line += f" | Sentiment: {sentiment}"

        line += f" | Important: {important}"

        if score is not None:
            line += f" | Similarity Score: {score}"

        lines.append(line)

    return "\n".join(lines)


def build_context(state: AgentState) -> AgentState:
    """Combine structured and semantic memory into one context string."""

    print("[LangGraph] Building final context...")

    try:
        driver_data = state.get("driver_data") or {}
        payments = state.get("payments") or []
        tickets = state.get("tickets") or []
        semantic_memories = state.get("semantic_memories") or []
        is_new_driver = state.get("new_driver", False)

        context_sections = [
            "SIGNO DRIVER MEMORY CONTEXT",
            "",
        ]

        if is_new_driver or (not payments and not tickets and not semantic_memories):
            context_sections.extend(
                [
                    "New Driver Detected",
                    "No previous payments, tickets, or semantic memories were found.",
                    "",
                ]
            )

        context_sections.extend(
            [
                _format_key_values("Driver Info", driver_data),
                "",
                _format_list("Recent Payments", payments),
                "",
                _format_list("Open Tickets", tickets),
                "",
                _format_semantic_memories(semantic_memories),
            ]
        )

        final_context = "\n".join(context_sections)

        print("[LangGraph] Final context built.")
        return {"final_context": final_context}

    except Exception as error:
        print(f"[LangGraph] Error building final context: {error}")
        return {"final_context": "Unable to build memory context."}
