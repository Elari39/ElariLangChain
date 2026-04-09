from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os

load_dotenv(encoding='utf-8',override=True)

gemini3flash=init_chat_model(
    model_provider="openai",
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("OPENAI_CHAT_MODEL"),
    temperature=0.0,
    max_tokens=4096
)

deepseek=init_chat_model(
    model_provider="openai",
    base_url="https://api.deepseek.com/v1",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    model="deepseek-chat",
    temperature=0.0,
    max_tokens=4096
)

minimax=init_chat_model(
    model_provider="openai",
    base_url=os.getenv("MINIMAX_BASE_URL"),
    api_key=os.getenv("MINIMAX_API_KEY"),
    model=os.getenv("MINIMAX_MODEL"),
    temperature=0.0,
    max_tokens=4096
)