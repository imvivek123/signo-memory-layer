"""LangGraph flow for retrieving memory before or during a call."""

from langgraph.graph import END, START, StateGraph

from nodes.build_context import build_context
from nodes.fetch_structured_memory import fetch_structured_memory
from nodes.identify_driver import identify_driver
from state.agent_state import AgentState


def build_fetch_memory_graph():
    """Build and compile the during-call memory retrieval graph."""

    graph = StateGraph(AgentState)

    graph.add_node("identify_driver", identify_driver)
    graph.add_node("fetch_structured_memory", fetch_structured_memory)
    graph.add_node("build_context", build_context)

    graph.add_edge(START, "identify_driver")
    graph.add_edge("identify_driver", "fetch_structured_memory")
    graph.add_edge("fetch_structured_memory", "build_context")
    graph.add_edge("build_context", END)

    return graph.compile()


fetch_memory_graph = build_fetch_memory_graph()
