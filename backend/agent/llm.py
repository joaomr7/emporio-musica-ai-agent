from langchain_openai import ChatOpenAI

from backend.config import settings

def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        temperature=0,
        timeout=120,
        max_retries=1
    )