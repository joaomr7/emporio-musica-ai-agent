import hashlib
import json

def build_product_text(product) -> str:
    specs = json.dumps(product.specs or {}, ensure_ascii=False, sort_keys=True)

    return (
        f'Nome: {product.name}\n'
        f'Categoria: {product.category.name}\n'
        f'Descrição: {product.description or ""}\n'
        f'Especificações: {specs}'
    )

def get_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()