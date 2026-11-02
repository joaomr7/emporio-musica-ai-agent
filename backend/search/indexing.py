import asyncio

from tortoise import connections

from backend.database import close_db, init_db
from backend.models import Product, ProductSearchIndex
from backend.search.documents import build_product_text, get_content_hash
from backend.search.embeddings import MODEL_VERSION, encode_documents

BATCH_SIZE = 32

UPSERT_SQL = '''
    INSERT INTO product_search_index (
        product_id, search_text, embedding, content_hash, model_version, indexed_at
    )
    VALUES ($1, $2, $3::vector, $4, $5, NOW())
    ON CONFLICT (product_id) DO UPDATE SET
        search_text = EXCLUDED.search_text,
        embedding = EXCLUDED.embedding,
        content_hash = EXCLUDED.content_hash,
        model_version = EXCLUDED.model_version,
        indexed_at = NOW()
'''

def serialize_vector(vector: list[float]) -> str:
    return '[' + ','.join(str(value) for value in vector) + ']'

async def index_products(batch_size: int = BATCH_SIZE) -> dict:
    if batch_size < 1:
        raise ValueError('batch_size must be greater than zero')

    connection = connections.get('default')
    last_id = 0
    indexed = 0
    unchanged = 0

    while True:
        products = await (
            Product.filter(product_id__gt=last_id)
            .select_related('category')
            .order_by('product_id')
            .limit(batch_size)
        )

        if not products:
            break

        last_id = products[-1].product_id
        product_ids = [product.product_id for product in products]

        existing = await ProductSearchIndex.filter(
            product_id__in=product_ids
        ).values('product_id', 'content_hash', 'model_version')

        existing_by_id = {item['product_id']: item for item in existing}
        pending = []

        for product in products:
            text = build_product_text(product)
            content_hash = get_content_hash(text)
            current = existing_by_id.get(product.product_id)

            if current and current['content_hash'] == content_hash and current['model_version'] == MODEL_VERSION:
                unchanged += 1
                continue

            pending.append((product.product_id, text, content_hash))

        if not pending:
            continue

        vectors = await encode_documents([item[1] for item in pending])

        rows = [
            [product_id, text, serialize_vector(vector), content_hash, MODEL_VERSION]
            for (product_id, text, content_hash), vector in zip(pending, vectors)
        ]

        await connection.execute_many(UPSERT_SQL, rows)
        indexed += len(rows)

        print(f'Indexed: {indexed} | Unchanged: {unchanged}')

    return {'indexed': indexed, 'unchanged': unchanged}

async def main():
    await init_db()

    try:
        result = await index_products()
        print(f'Indexing complete: {result}')
    finally:
        await close_db()

if __name__ == '__main__':
    asyncio.run(main())
