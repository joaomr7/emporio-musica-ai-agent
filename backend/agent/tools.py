import json
from decimal import Decimal
from pathlib import Path

from langchain.tools import ToolRuntime, tool

from backend.agent.context import AgentContext
from backend.models import Category, Order, Product

POLICIES_PATH = Path(__file__).resolve().parent.parent / 'policies' / 'store.json'

@tool
async def list_categories() -> str:
    '''Consulte os tipos de instrumentos do catálogo e seus IDs antes de filtrar produtos por categoria.

    Não recebe parâmetros. Retorna uma string JSON contendo uma lista ordenada por nome,
    com category_id (inteiro), name (nome) e description (descrição ou null). Use o category_id retornado
    em search_products.
    '''
    categories = await Category.all().order_by('name')

    return json.dumps([
        {
            'category_id': category.category_id,
            'name': category.name,
            'description': category.description
        }
        for category in categories
    ], ensure_ascii=False)


@tool
async def search_products(
    query: str = '',
    category_id: int | None = None,
    max_price: float | None = None,
    available_only: bool = True,
    limit: int = 10,
    offset: int = 0
) -> str:
    '''Busque e compare produtos por nome, categoria, orçamento ou disponibilidade.

    Parâmetros: query é um trecho do nome, sem distinção entre maiúsculas e minúsculas
    (ex.: Yamaha ou C40); não pesquisa descrição ou specs. Para tipos de instrumento,
    consulte list_categories e informe category_id em vez de usar uma categoria genérica
    em query. query vazio não restringe o nome. max_price é o preço máximo inclusivo em
    reais, não negativo; null não restringe o preço. available_only=True retorna apenas
    produtos ativos com estoque positivo; False inclui também inativos e sem estoque.
    Os filtros informados são combinados. limit aceita 1 a 30 (padrão 10) e offset é a
    quantidade de resultados a pular, não negativa (padrão 0).

    Retorna uma string JSON com total, limit, offset, has_more, next_offset e products.
    Cada produto contém product_id, name, category (nome), description, price_brl,
    stock_quantity e specs (dados técnicos ou null).
    Para continuar, mantenha os filtros e use next_offset quando has_more=True.
    '''
    if not 1 <= limit <= 30:
        return 'O limite deve estar entre 1 e 30.'

    if offset < 0:
        return 'O offset não pode ser negativo.'

    products = Product.all().select_related('category')

    if query:
        products = products.filter(name__icontains=query.strip())

    if category_id is not None:
        products = products.filter(category_id=category_id)

    if max_price is not None:
        if max_price < 0:
            return 'O preço máximo não pode ser negativo.'

        products = products.filter(price_brl__lte=Decimal(str(max_price)))

    if available_only:
        products = products.filter(stock_quantity__gt=0, status='active')

    total = await products.count()
    results = await products.order_by('price_brl', 'product_id').offset(offset).limit(limit)

    return json.dumps({
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
    }, ensure_ascii=False)

@tool
async def get_product(product_id: int) -> str:
    '''Consulte os detalhes e as promoções ativas de um produto específico.

    product_id é o ID inteiro obtido em search_products; se você só conhece o nome,
    busque o produto primeiro. Retorna uma string JSON com product_id, name, category
    (nome), description, price_brl, stock_quantity, status, specs (dados técnicos ou null) e promotions.
    promotions contém apenas promoções marcadas como ativas, cada uma com
    discount_percent e description.
    O retorno não calcula o preço com desconto nem valida regras de acúmulo; consulte
    get_policy com topic=promotions para essas regras. Pode retornar produtos inativos
    ou sem estoque.
    '''
    product = await Product.get_or_none(product_id=product_id).select_related('category')

    if product is None:
        return 'Produto não encontrado.'

    promotions = await product.promotions.filter(is_active=True)

    return json.dumps({
        'product_id': product.product_id,
        'name': product.name,
        'category': product.category.name,
        'description': product.description,
        'price_brl': str(product.price_brl),
        'stock_quantity': product.stock_quantity,
        'status': product.status,
        'specs': product.specs,
        'promotions': [
            {
                'discount_percent': str(promotion.discount_percent),
                'description': promotion.description
            }
            for promotion in promotions
        ]
    }, ensure_ascii=False)

@tool
async def get_my_orders(runtime: ToolRuntime[AgentContext], limit: int = 10, offset: int = 0) -> str:
    '''Liste os pedidos do cliente atual com paginação ou descubra o ID de uma compra.

    limit aceita 1 a 30 (padrão 10) e offset é a quantidade de pedidos a pular, não negativa (padrão 0).
    Retorna uma string JSON com total (total de pedidos do cliente), limit, offset,
    has_more, next_offset (próximo deslocamento ou null) e orders (pedidos desta página).
    Os pedidos são ordenados do mais recente para o mais antigo, com order_id,
    order_date (YYYY-MM-DD), status e total_brl.
    Para continuar, use next_offset quando has_more=True, mantendo o mesmo limit.
    '''
    if not 1 <= limit <= 30:
        return 'O limite deve estar entre 1 e 30.'

    if offset < 0:
        return 'O offset não pode ser negativo.'

    orders = Order.filter(customer_id=runtime.context.customer_id)
    total = await orders.count()
    results = await orders.order_by('-order_date', '-order_id').offset(offset).limit(limit)

    return json.dumps({
        'total': total,
        'limit': limit,
        'offset': offset,
        'has_more': offset + len(results) < total,
        'next_offset': offset + len(results) if offset + len(results) < total else None,
        'orders': [
            {
                'order_id': order.order_id,
                'order_date': order.order_date.isoformat(),
                'status': order.status,
                'total_brl': str(order.total_brl)
            }
            for order in results
        ]
    }, ensure_ascii=False)

@tool
async def get_order(order_id: int, runtime: ToolRuntime[AgentContext]) -> str:
    '''Consulte itens, pagamento, status e rastreamento de um pedido do cliente atual.

    order_id é o ID inteiro da compra, informado pelo cliente ou obtido em get_my_orders.
    Retorna uma string JSON com order_id, order_date (YYYY-MM-DD), status, total_brl,
    payment_method (código da forma de pagamento),
    tracking_code, estimated_delivery (YYYY-MM-DD ou null), notes e items.
    Cada item contém product_id, name e quantity. tracking_code e notes podem ser null.
    '''
    
    order = await Order.get_or_none(
        order_id=order_id,
        customer_id=runtime.context.customer_id
    )

    if order is None:
        return 'Pedido não encontrado para este cliente.'

    items = await order.items.all().select_related('product')

    return json.dumps({
        'order_id': order.order_id,
        'order_date': order.order_date.isoformat(),
        'status': order.status,
        'total_brl': str(order.total_brl),
        'payment_method': order.payment_method,
        'tracking_code': order.tracking_code,
        'estimated_delivery': order.estimated_delivery.isoformat() if order.estimated_delivery else None,
        'notes': order.notes,
        'items': [
            {
                'product_id': item.product_id,
                'name': item.product.name,
                'quantity': item.quantity
            }
            for item in items
        ]
    }, ensure_ascii=False)

@tool
def get_policy(topic: str) -> str:
    '''Consulte informações oficiais e regras gerais da loja por tópico.

    Informe topic exatamente como uma destas chaves:
    - store: nome, endereço, telefone, horários e ramo de atuação.
    - payment: formas de pagamento, desconto no Pix, parcelamento e ressalvas.
    - returns: prazos para arrependimento, reembolso e troca por defeito.
    - shipping: condições e valores de frete, transportadoras e prazos gerais.
    - promotions: regras de acúmulo de descontos e condições das promoções.
    - service: canais de atendimento e tratamento e prazo de resposta a reclamações.
    - warranty: prazo de garantia legal, garantia do fabricante e exclusões.
    - privacy: uso dos dados pessoais, consentimento e solicitação de exclusão.

    Retorna uma string JSON com o objeto do tópico solicitado, contendo suas regras.
    '''
    with POLICIES_PATH.open(encoding='utf-8') as file:
        policies = json.load(file)

    policy = policies.get(topic)

    if policy is None:
        return json.dumps({
            'error': 'Política não encontrada',
            'available_topics': list(policies)
        }, ensure_ascii=False)

    return json.dumps(policy, ensure_ascii=False)

tools = [
    list_categories,
    search_products,
    get_product,
    get_my_orders,
    get_order,
    get_policy
]
