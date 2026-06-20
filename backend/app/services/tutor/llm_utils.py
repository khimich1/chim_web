"""Shared LLM invoke/stream helpers for tutor graph nodes."""

from __future__ import annotations

from functools import reduce
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_openai import ChatOpenAI

if TYPE_CHECKING:
    from app.services.tutor.context import TutorRunContext


def chunk_text(message: AIMessage | AIMessageChunk) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "".join(parts)
    return ""


def invoke_llm(llm: ChatOpenAI, messages: list, ctx: TutorRunContext) -> AIMessage:
    """Invoke or stream the LLM; optional stream_sink emits token chunks (Task 47 U1)."""
    if ctx.stream_sink is None:
        response = llm.invoke(messages)
        if isinstance(response, AIMessage):
            return response
        return AIMessage(content=str(response.content))

    chunks: list[AIMessageChunk] = []
    for chunk in llm.stream(messages):
        if not isinstance(chunk, AIMessageChunk):
            continue
        text = chunk_text(chunk)
        if text:
            ctx.stream_sink(text)
        chunks.append(chunk)
    if not chunks:
        response = llm.invoke(messages)
        return response if isinstance(response, AIMessage) else AIMessage(content=str(response.content))
    merged = reduce(lambda left, right: left + right, chunks)
    return AIMessage(content=chunk_text(merged) or str(merged.content))
