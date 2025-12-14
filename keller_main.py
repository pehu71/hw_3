import asyncio
import os
from typing import Annotated
from dotenv import load_dotenv
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
import json
from langchain_core.messages import ToolMessage
from typing import Literal
from visualizer import visualize

load_dotenv()

# Model
llm = ChatOpenAI(model="gpt-5-mini")


# ============================================================================
# MCP CLIENT SETUP
# ============================================================================


def get_tavily_mcp_url():
    """Get Tavily MCP URL with API key."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not found in environment")
    return f"https://mcp.tavily.com/mcp/?tavilyApiKey={api_key}"


async def get_mcp_tools():
    """Load tools from Tavily MCP server."""
    client = MultiServerMCPClient(
        {
            "tavily": {
                "url": get_tavily_mcp_url(),
                "transport": "streamable_http",
            }
        }
    )
    tools = await client.get_tools()
    return tools, client


# Global variable to store all tools
all_tools = None


# Custom Tools
@tool
def get_food() -> str:
    """Get a plate of spaghetti."""
    return "Here is your plate of spaghetti 🍝"


# ---------------------------
# Define the graph
# ---------------------------


# State
class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


# Node 1 ----------
def chatbot(state: State):
    global all_tools
    llm_with_tools = llm.bind_tools(all_tools)
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


# Node 2 ----------
class BasicToolNode:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    async def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = await self.tools_by_name[tool_call["name"]].ainvoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}


# Edge 1 -------------------


def route_tools(
    state: State,
) -> Literal["tools", "__end__"]:
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        print("Routing to tools")
        print("Tool calls found:", ai_message.tool_calls)
        return "tools"
    return "__end__"


async def main():
    """Main async function to initialize and run the graph."""
    global all_tools

    # Initialize MCP tools
    print("Initializing MCP connection to Tavily...")
    mcp_tools, mcp_client = await get_mcp_tools()
    print(f"Loaded {len(mcp_tools)} tools from Tavily MCP\n")

    # Combine all tools
    all_tools = list(mcp_tools) + [get_food]

    # Initialize tool node
    tool_node = BasicToolNode(tools=all_tools)

    # Build graph
    graph_builder = StateGraph(State)

    # The first argument is the unique node name
    # The second argument is the function or object that will be called whenever
    # the node is used.
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", tool_node)

    # The `tools_condition` function returns "tools" if the chatbot asks to use a tool, and "__end__" if
    # it is fine directly responding. This conditional routing defines the main agent loop.
    graph_builder.add_conditional_edges(
        "chatbot",
        route_tools,
        # The following dictionary lets you tell the graph to interpret the condition's outputs as a specific node
        # It defaults to the identity function, but if you
        # want to use a node named something else apart from "tools",
        # You can update the value of the dictionary to something else
        # e.g., "tools": "my_tools"
        {"tools": "tools", "__end__": "__end__"},
    )
    # Any time a tool is called, we return to the chatbot to decide the next step
    graph_builder.add_edge("tools", "chatbot")

    # Entry and finish points
    graph_builder.set_entry_point("chatbot")

    # Graph object
    graph = graph_builder.compile()

    # Visualize the graph
    visualize(graph, "graph.png")

    # ---------------------------
    # Run the graph
    # MESSAGES are stored ONLY within the graph state !!!!
    # EACH USER INPUT IS A NEW STATE !!!!
    # =>  NO HISTORY for chat interaction !!!!!!
    # ---------------------------
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        async for event in graph.astream({"messages": ("user", user_input)}):
            for value in event.values():
                print("Assistant:", value["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
