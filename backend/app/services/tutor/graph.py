"""LangGraph agent graph for the chemistry tutor (ported from RAG_chemistry)."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, SystemMessage
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
    tool_output_guard,
)
from app.services.tutor.llm_utils import invoke_llm
from app.services.tutor.memory import load_profile
from app.services.tutor.prompts import build_system_prompt
from app.services.tutor.solve.critic import (
    make_answer_finalize_node,
    make_critic_node,
    route_after_critic,
)
from app.services.tutor.solve.intent_router import route_intent
from app.services.tutor.solve.prepare_context import (
    make_prepare_context_node,
    route_after_prepare_context,
)
from app.services.tutor.solve.solver import make_solver_node
from app.services.tutor.solve.state import SolveState
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
        response = invoke_llm(bound, messages, ctx)
        return {"messages": [response]}

    return agent_node


def route_after_agent(state: MessagesState) -> str:
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END


def route_after_input_guard(state: MessagesState, ctx: TutorRunContext) -> str:
    """Off-topic → END; solve intent → prepare_context; else general agent."""
    last = state["messages"][-1]
    if isinstance(last, AIMessage):
        return END
    if route_intent(state, ctx) == "solve_pipeline":
        return "prepare_context"
    return "agent"


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

    builder = StateGraph(SolveState)
    builder.add_node("input_guard", make_input_guard(is_on_topic))
    builder.add_node("agent", make_agent_node(llm, ctx, tools))
    builder.add_node("tools", ToolNode(tools))
    builder.add_node("tool_output_guard", tool_output_guard)
    builder.add_node("prepare_context", make_prepare_context_node(ctx))
    builder.add_node("solver", make_solver_node(llm, ctx))
    builder.add_node("critic", make_critic_node())
    builder.add_node("answer_finalize", make_answer_finalize_node())

    builder.add_edge(START, "input_guard")
    builder.add_conditional_edges(
        "input_guard",
        lambda state: route_after_input_guard(state, ctx),
        {
            END: END,
            "agent": "agent",
            "prepare_context": "prepare_context",
        },
    )
    builder.add_conditional_edges(
        "prepare_context",
        route_after_prepare_context,
        {"end": END, "solver": "solver"},
    )
    builder.add_edge("solver", "critic")
    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {"end": END, "solver": "solver", "answer_finalize": "answer_finalize"},
    )
    builder.add_edge("answer_finalize", END)
    builder.add_conditional_edges(
        "agent",
        route_after_agent,
        {"tools": "tools", END: END},
    )
    builder.add_edge("tools", "tool_output_guard")
    builder.add_edge("tool_output_guard", "agent")

    return builder.compile(checkpointer=checkpointer)
