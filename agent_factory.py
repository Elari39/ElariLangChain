import os
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from agent_tools import Context, build_tools


SYSTEM_PROMPT = "你是我的人工智能助手，协助我解答问题和提供信息。请根据我的提问，结合你的知识库和工具，给出准确、简洁的回答。如果需要使用工具，请合理调用，并将结果整合到最终回答中。无论如何，请确保你的回答清晰、有条理，并且直接回应我的问题。保存图片的时候，图片名称按照对应平台+链接编号的格式命名"


def build_agent() -> Any:
    load_dotenv(encoding="utf-8", override=True)
    store = InMemoryStore()
    checkpointer = InMemorySaver()
    model = init_chat_model(
    model_provider="openai",
    base_url=os.getenv("MINIMAX_BASE_URL"),
    api_key=os.getenv("MINIMAX_API_KEY"),
    model=os.getenv("MINIMAX_MODEL"),
    temperature=0.3,
    max_tokens=8192
)
    return create_agent(
        model=model,
        tools=build_tools(),
        checkpointer=checkpointer,
        store=store,
        context_schema=Context,
        system_prompt=SYSTEM_PROMPT,
    )


def build_runtime_context(user_id: str) -> Context:
    return Context(user_id=user_id)


def build_config(thread_id: str) -> dict[str, dict[str, str]]:
    return {"configurable": {"thread_id": thread_id}}
