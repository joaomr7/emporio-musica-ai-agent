import json
from pathlib import Path

from langchain.tools import ToolRuntime, tool

from backend.agent.context import AgentContext
from backend.models import Category, Order, Product
from backend.search.retrieval import search_products as retrieve_products

POLICIES_PATH = Path(__file__).resolve().parent.parent / 'policies' / 'store.json'

@tool
async def list_categories() -> str:
    '''Lista as categorias de instrumentos disponíveis no catálogo.

    Use para conhecer os tipos de instrumentos vendidos ou obter o category_id
    necessário para filtrar search_products. Retorna category_id, name e description.
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
    '''Busca produtos no catálogo com filtros e paginação.

    Use query para buscas por nome, marca, características ou finalidade.
    Sem query, aplica filtros estruturados e ordena por preço.

    category_id filtra a categoria, max_price limita o preço e
    available_only restringe a produtos ativos com estoque.

    limit define a quantidade de resultados (1 a 30) e offset a posição inicial.
    Use next_offset para consultar outras páginas.

    Resultados semânticos são aproximações; não assuma que todas as características
    solicitadas estão presentes. Para detalhes ou promoções, use get_product.
    '''
    limit = max(1, min(limit, 30))
    offset = max(0, offset)

    result = await retrieve_products(
        query=query,
        category_id=category_id,
        max_price=max_price,
        available_only=available_only,
        limit=limit,
        offset=offset
    )

    return json.dumps(result, ensure_ascii=False)

@tool
async def get_product(product_id: int) -> str:
    '''Consulta informações detalhadas e promoções ativas de um produto.

    Use product_id obtido em search_products. Se conhecer apenas o nome,
    busque o produto antes.

    Retorna identificação, nome, categoria, descrição, preço, estoque,
    status, especificações técnicas e promoções ativas.

    O preço retornado é o preço cadastrado, sem aplicação automática
    de descontos. Consulte get_policy(topic='promotions') para regras comerciais.

    Não considere produtos inativos ou sem estoque como disponíveis para compra.
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
    '''Lista os pedidos pertencentes ao cliente autenticado no contexto.

    Use para consultar compras anteriores ou localizar um pedido.
    Retorna data, status, total e identificador de cada pedido.

    Aceita limit de 1 a 30 e offset a partir de zero.
    Use next_offset quando has_more for verdadeiro.
    Para detalhes de uma compra, utilize get_order.

    O cliente é identificado automaticamente pelo contexto.
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
    '''Consulta os detalhes de um pedido pertencente ao cliente atual.

    Use order_id informado pelo cliente ou obtido em get_my_orders.

    Retorna itens, status, pagamento, total, rastreamento e previsão
    de entrega, quando disponíveis.

    A previsão de entrega não comprova que o pedido foi entregue.
    Campos ausentes ou nulos não devem ser presumidos.
    O acesso é restrito aos pedidos do cliente atual.
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
    '''Consulta as políticas e informações cadastradas da loja.

    Informe topic com uma das seguintes opções:
    - store: endereço, contato e funcionamento.
    - payment: formas de pagamento e parcelamento.
    - returns: arrependimento, devoluções e reembolsos.
    - shipping: frete e estimativas de entrega.
    - promotions: descontos e condições promocionais.
    - service: canais de atendimento e reclamações.
    - warranty: garantia e tratamento de defeitos.
    - privacy: tratamento de dados pessoais.

    Retorna as informações cadastradas para o tópico solicitado.

    Informe somente condições explicitamente previstas no retorno.
    Não presuma prazos, valores, exceções ou garantias ausentes.
    Se faltar uma condição essencial, indique que precisa ser confirmada.
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
