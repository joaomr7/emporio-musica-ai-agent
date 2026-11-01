import asyncio
import csv
import json
from pathlib import Path

from tortoise.transactions import in_transaction

from backend.database import close_db, init_db
from backend.models import Category, Customer, Order, OrderItem, Product, Promotion

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

def read_csv(filename: str) -> list[dict]:
    with (DATA_DIR / filename).open(encoding='utf-8-sig', newline='') as file:
        return list(csv.DictReader(file))

def optional(value: str):
    return value if value else None

async def upsert(model, rows: list[dict], key: str):
    for row in rows:
        identifier = row.pop(key)
        await model.update_or_create(defaults=row, **{key: identifier})

async def import_data():
    categories = read_csv('categories.csv')
    customers = read_csv('customers.csv')
    products = read_csv('products.csv')
    orders = read_csv('orders.csv')
    promotions = read_csv('promotions.csv')
    order_items = read_csv('order_items.csv')

    for row in products:
        row['specs'] = json.loads(row['specs'])

    for row in promotions:
        row['is_active'] = bool(int(row['is_active']))

    for row in orders:
        for field in ('tracking_code', 'estimated_delivery', 'notes'):
            row[field] = optional(row[field])

    for row in order_items:
        row['quantity'] = int(row['quantity'])

    await init_db()

    try:
        async with in_transaction():
            await upsert(Category, categories, 'category_id')
            await upsert(Customer, customers, 'customer_id')
            await upsert(Product, products, 'product_id')
            await upsert(Order, orders, 'order_id')
            await upsert(Promotion, promotions, 'promotion_id')

            for row in order_items:
                await OrderItem.update_or_create(order_id=row['order_id'], product_id=row['product_id'], defaults={'quantity': row['quantity']})
    finally:
        await close_db()

if __name__ == '__main__':
    asyncio.run(import_data())