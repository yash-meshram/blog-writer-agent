from langgraph.graph import END, StateGraph
# from services.nodes import router, route_next, researcher, orchestrator, fanout, worker, merge_content, decide_images, generate_and_place_images
from schemas.schema import State

from services.temp_nodes import generate_and_place_images

# # build reducer subgraph
# reducer_graph = StateGraph(State)
# reducer_graph.add_node("merge_content", merge_content)
# reducer_graph.add_node("decide_images", decide_images)
# reducer_graph.add_node("generate_and_place_images", generate_and_place_images)

# reducer_graph.set_entry_point("merge_content")
# reducer_graph.add_edge("merge_content", "decide_images")
# reducer_graph.add_edge("decide_images", "generate_and_place_images")
# reducer_graph.add_edge("generate_and_place_images", END)

# reducer_graph = reducer_graph.compile()


# graph = StateGraph(State)

# graph.add_node("router", router)
# graph.add_node("researcher", researcher)
# graph.add_node("orchestrator", orchestrator)
# graph.add_node("worker", worker)
# graph.add_node("reducer", reducer_graph)

# graph.set_entry_point("router")
# graph.add_conditional_edges("router", route_next, {"researcher": "researcher", "orchestrator": "orchestrator"})
# graph.add_edge("researcher", "orchestrator")
# graph.add_conditional_edges("orchestrator", fanout, ["worker"])
# graph.add_edge("worker", "reducer")
# graph.add_edge("reducer", END)

# Temp
graph = StateGraph(State)
graph.add_node("generate_and_place_images", generate_and_place_images)
graph.set_entry_point("generate_and_place_images")
graph.add_edge("generate_and_place_images", END)
app = graph.compile()