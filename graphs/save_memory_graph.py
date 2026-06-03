"""LangGraph flow for saving compressed memory after a call ends.

The save graph receives only one business payload: compressed_memory.
Raw OmniDimension webhook fields are parsed before this graph and are not
passed into the persistence nodes.
"""

from langgraph.graph import END, START, StateGraph

from nodes.identify_driver import identify_driver
from nodes.save_postgresql_memory import save_postgresql_memory
from nodes.save_semantic_memory import save_semantic_memory
from state.agent_state import AgentState


def build_save_memory_graph():
    """Build and compile the compressed-memory saving graph."""

    graph = StateGraph(AgentState)

    graph.add_node("identify_driver", identify_driver)
    graph.add_node("save_postgresql_memory", save_postgresql_memory)
    graph.add_node("save_semantic_memory", save_semantic_memory)

    graph.add_edge(START, "identify_driver")
    graph.add_edge("identify_driver", "save_postgresql_memory")
    graph.add_edge("save_postgresql_memory", "save_semantic_memory")
    graph.add_edge("save_semantic_memory", END)

    return graph.compile()


save_memory_graph = build_save_memory_graph()
