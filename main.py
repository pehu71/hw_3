from read_db import get_movies_by_actor, get_movies_by_title, get_movies_by_director, get_movies_by_year, get_movies_by_genre
from utils import print_banner
import asyncio
import os
import json
from typing import Annotated
from dotenv import load_dotenv
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from typing import Literal
from visualizer import visualize
from langchain_core.messages import SystemMessage


load_dotenv()

# Model
llm = ChatOpenAI(model="gpt-5-mini", api_key=os.getenv("OPENAI_API_KEY"))

# Global variable to store all tools
all_tools = None

# Custom Tools
@tool("get_movies_by_actor", description="Use this tool whenever the user asks for movies by actor.")
def get_movies_by_actor_tool(actor: str) -> str:
    return get_movies_by_actor(actor)

@tool("get_movies_by_title", description="Use this tool whenever the user asks for movies by title.")
def get_movies_by_title_tool(title: str) -> str:
    return get_movies_by_title(title)

@tool("get_movies_by_director", description="Use this tool whenever the user asks for movies by director.")
def get_movies_by_director_tool(director: str) -> str:
    return get_movies_by_director(director)

@tool("get_movies_by_year", description="Use this tool whenever the user asks for movies by year.")
def get_movies_by_year_tool(year: int) -> str:
    return get_movies_by_year(year)

@tool("get_movies_by_genre", description="Use this tool whenever the user asks for movies by genre.")
def get_movies_by_genre_tool(genre: str) -> str:
    return get_movies_by_genre(genre)

# ---------------------------
# Define the graph
# ---------------------------

# State
class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]

# system prompt with some instructions
SYSTEM_PROMPT = """
You are a movie database assistant.

Rules:
- ALWAYS use the provided tools when the user asks about movies.
- NEVER use your own knowledge.
- Base your answers ONLY on tool results.
- If no data is found, explicitly say so.
- Do not guess or hallucinate.
"""

# Node 1 ----------
def chatbot(state: State):
    global all_tools
    llm_with_tools = llm.bind_tools(all_tools)

    messages = state["messages"]

    # sanitize input by adding system prompt if missing
    if not messages or messages[0].type != "system":
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    return {"messages": [llm_with_tools.invoke(messages)]}

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
    
def route_tools(state: State) -> Literal["tools", "__end__"]:
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
    # Print intro banner
    print_banner()
    global all_tools
    
    # Define all tools
    all_tools = [
        get_movies_by_actor_tool,
        get_movies_by_title_tool,
        get_movies_by_director_tool,
        get_movies_by_year_tool,
        get_movies_by_genre_tool
        ]
    
    # Initialize tool node
    tool_node = BasicToolNode(tools=all_tools)

    # Define the graph
    graph_builder = StateGraph(State)

    # Add nodes
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", tool_node)

    # Conditional edge: from chatbot to tools or end
    graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    {"tools": "tools", "__end__": "__end__"},
    )

    # Any time a tool is called, we return to the chatbot to decide the next step
    graph_builder.add_edge("tools", "chatbot")

    # Entry and finish points
    graph_builder.set_entry_point("chatbot")

    # Graph object
    graph = graph_builder.compile()

    # Visualize the graph
    visualize(graph, "movie_agent_graph.png")

    # ---------------------------
    # Run the graph
    # ---------------------------
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Hope you enjoy a nice flick tonite:-) Goodbye!")
            break
        async for event in graph.astream({"messages": ("user", user_input)}):
            for value in event.values():
                print("Assistant:", value["messages"][-1].content)    

if __name__ == "__main__":
    asyncio.run(main())
