from functools import lru_cache

from langchain_openai import OpenAIEmbeddings

from backend.config import settings

EMBEDDING_DIMENSIONS = settings.embedding_dimensions
MODEL_VERSION = f'{settings.embedding_model}:product-v1'

@lru_cache(maxsize=1)
def get_embeddings():
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        dimensions=EMBEDDING_DIMENSIONS,
        check_embedding_ctx_length=False,
        chunk_size=32
    )

async def encode_documents(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    vectors = await get_embeddings().aembed_documents(texts)

    if len(vectors) != len(texts) or any(len(vector) != EMBEDDING_DIMENSIONS for vector in vectors):
        raise ValueError('Incompatible number or dimension of embeddings')

    return vectors

async def encode_query(query: str) -> list[float]:
    vector = await get_embeddings().aembed_query(query)

    if len(vector) != EMBEDDING_DIMENSIONS:
        raise ValueError(f'Embedding dimension incompatible with VECTOR({EMBEDDING_DIMENSIONS})')

    return vector