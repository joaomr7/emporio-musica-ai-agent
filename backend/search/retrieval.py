from decimal import Decimal

from tortoise import connections

from backend.search.embeddings import encode_query
from backend.models import Product

SEARCH_SQL = '''
    SELECT
        p.product_id,
        p.name,
        p.description,
        p.price_brl,
        p.stock_quantity,
        p.status,
        p.specs,
        c.name AS category,
        1 - (i.embedding <=> $1::vector) AS similarity
    FROM product_search_index i
    JOIN products p ON p.product_id = i.product_id
    JOIN categories c ON c.category_id = p.category_id
    WHERE ($2::int IS NULL OR p.category_id = $2)
      AND ($3::numeric IS NULL OR p.price_brl <= $3)
      AND ($4::boolean = FALSE OR (p.stock_quantity > 0 AND p.status = 'active'))
    ORDER BY i.embedding <=> $1::vector, p.product_id
    LIMIT $5 OFFSET $6
'''

COUNT_SQL = '''
    SELECT COUNT(*) AS total
    FROM product_search_index i
    JOIN products p ON p.product_id = i.product_id
    WHERE ($1::int IS NULL OR p.category_id = $1)
      AND ($2::numeric IS NULL OR p.price_brl <= $2)
      AND ($3::boolean = FALSE OR (p.stock_quantity > 0 AND p.status = 'active'))
'''

def serialize_vector(vector: list[float]) -> str:
    return '[' + ','.join(str(value) for value in vector) + ']'

async def search_products(
    query: str,
    category_id: int | None = None,
    max_price: float | None = None,
    available_only: bool = True,
    limit: int = 10,
    offset: int = 0
) -> dict:
    if not 1 <= limit <= 30 or offset < 0:
        raise ValueError('Invalid pagination')

    if max_price is not None and max_price < 0:
        raise ValueError('max_price must be greater or equal to 0')

    if not query.strip():
        products = Product.all().select_related('category')

        if category_id is not None:
            products = products.filter(category_id=category_id)

        if max_price is not None:
            products = products.filter(price_brl__lte=Decimal(str(max_price)))

        if available_only:
            products = products.filter(stock_quantity__gt=0, status='active')

        total = await products.count()
        results = await products.order_by('price_brl', 'product_id').offset(offset).limit(limit)

        return {
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': offset + len(results) < total,
            'next_offset': offset + len(results) if offset + len(results) < total else None,
            'products': [
                {
                    'product_id': product.product_id,
                    'name': product.name,
                    'category': product.category.name,
                    'description': product.description,
                    'price_brl': str(product.price_brl),
                    'stock_quantity': product.stock_quantity,
                    'specs': product.specs
                }
                for product in results
            ]
        }

    connection = connections.get('default')
    price = Decimal(str(max_price)) if max_price is not None else None
    vector = serialize_vector(await encode_query(query))

    total_result = await connection.execute_query_dict(
        COUNT_SQL, [category_id, price, available_only]
    )

    results = await connection.execute_query_dict(
        SEARCH_SQL, [vector, category_id, price, available_only, limit, offset]
    )

    total = total_result[0]['total']

    return {
        'total': total,
        'limit': limit,
        'offset': offset,
        'has_more': offset + len(results) < total,
        'next_offset': offset + len(results) if offset + len(results) < total else None,
        'products': [
            {
                **product,
                'price_brl': str(product['price_brl']),
                'similarity': float(product['similarity'])
            }
            for product in results
        ]
    }
