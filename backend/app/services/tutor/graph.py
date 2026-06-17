"""LangGraph agent graph for the chemistry tutor (ported from RAG_chemistry)."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from app.core.config import Settings, get_settings
from app.services.tutor.context import TutorRunContext, set_tutor_context
from app.services.tutor.guards import (
    make_input_guard,
    make_is_on_topic_checker,
    route_after_input_guard,
    tool_output_guard,
)
from app.services.tutor.memory import load_profile
from app.services.tutor.prompts import build_system_prompt
from app.services.tutor.tools import build_tools


def _build_llm(settings: Settings | None = None) -> ChatOpenAI:
    settings = settings or get_settings()
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=(
            SecretStr(settings.openai_api_key)
            if settings.openai_api_key
            else None
        ),
    )


def make_agent_node(llm: ChatOpenAI, ctx: TutorRunContext, tools: list):
    bound = llm.bind_tools(tools, parallel_tool_calls=False)

    def agent_node(state: MessagesState) -> dict:
        profile = load_profile(ctx.user_id)
        system_prompt = build_system_prompt(ctx, profile)
        messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
        response = bound.invoke(messages)
        return {"messages": [response]}

    return agent_node


def route_after_agent(state: MessagesState) -> str:
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END


def build_graph(
    ctx: TutorRunContext,
    llm: ChatOpenAI | None = None,
    *,
    settings: Settings | None = None,
    checkpointer: Any | None = None,
) -> CompiledStateGraph:
    """Compile the tutor agent graph.

    By default the graph is **stateless** (no checkpointer): multi-turn context
    is supplied by replaying the PostgreSQL transcript into ``invoke`` input
    (see ``TutorService.send_message``). PostgreSQL is the source of truth for
    history (spec ``docs/specs/tutor-rag.md`` §7, B1); an in-memory checkpointer
    would silently diverge across restarts and uvicorn workers.
    """
    set_tutor_context(ctx)
    llm = llm or _build_llm(settings)
    tools = build_tools(ctx)
    is_on_topic = make_is_on_topic_checker(llm)

    builder = StateGraph(MessagesState)
    builder.add_node("input_guard", make_input_guard(is_on_topic))
    builder.add_node("agent", make_agent_node(llm, ctx, tools))
    builder.add_node("tools", ToolNode(tools))
    builder.add_node("tool_output_guard", tool_output_guard)

    builder.add_edge(START, "input_guard")
    builder.add_conditional_edges(
        "input_guard",
        route_after_input_guard,
        {END: END, "agent": "agent"},
    )
    builder.add_conditional_edges(
        "agent",
        route_after_agent,
        {"tools": "tools", END: END},
    )
    builder.add_edge("tools", "tool_output_guard")
    builder.add_edge("tool_output_guard", "agent")

    return builder.compile(checkpointer=checkpointer)
