import asyncio

from backend.database import close_db, init_db
from backend.search.retrieval import search_products

async def main():
    await init_db()

    try:
        queries = [
            'violão para iniciantes com cordas de nylon',
            'Yamaha C40',
            'guitarra elétrica com captadores humbucker'
        ]

        for query in queries:
            result = await search_products(query, limit=5)

            print(f'\nQuery: {query}')
            print(f'Total: {result["total"]}')

            for product in result['products']:
                print(
                    f'{product["name"]} | '
                    f'R$ {product["price_brl"]} | '
                    f'Similarity: {product["similarity"]:.4f}'
                )

    finally:
        await close_db()

if __name__ == '__main__':
    asyncio.run(main())