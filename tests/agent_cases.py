AGENT_CASES = [
    {
        'name': 'Categorias disponíveis',
        'messages': [
            'Quais instrumentos vocês oferecem?'
        ],
        'expected': ['violões', 'guitarras', 'baterias'],
        'forbidden': ['erro no catálogo', 'inconsistência']
    },
    {
        'name': 'Marcas de baterias',
        'messages': [
            'Quais marcas de baterias vocês trabalham?'
        ],
        'expected': ['Yamaha', 'Pearl'],
        'forbidden': ['inconsistência', 'divergência']
    },
    {
        'name': 'Modelos de baterias',
        'messages': [
            'Quais marcas de baterias vocês trabalham?',
            'Quais são?'
        ],
        'expected': ['Yamaha Kit 1', 'Pearl Kit 2', 'Yamaha Kit 3'],
        'forbidden': [
            'inconsistência',
            'divergência',
            'erro interno',
            'confirme esses dados'
        ]
    },
    {
        'name': 'Parcelamento',
        'messages': [
            'É possível parcelar?'
        ],
        'expected': ['12', 'sem juros'],
        'forbidden': ['não sei', 'erro']
    },
    {
        'name': 'Desconto no PIX',
        'messages': [
            'Existe desconto para pagamento no PIX?'
        ],
        'expected': ['5%'],
        'forbidden': ['10%', '15%']
    },
    {
        'name': 'Acúmulo de descontos',
        'messages': [
            'Posso acumular o desconto do PIX com uma promoção?'
        ],
        'expected': ['não'],
        'forbidden': ['sim, pode']
    },
    {
        'name': 'Arrependimento de compra online',
        'messages': [
            'Comprei um instrumento pela internet. Qual o prazo para desistir?'
        ],
        'expected': ['7 dias', 'recebimento'],
        'forbidden': ['30 dias', '10 dias úteis']
    },
    {
        'name': 'Disponibilidade de produto',
        'messages': [
            'Vocês têm o violão Yamaha C40?'
        ],
        'expected': ['Yamaha C40'],
        'forbidden': ['erro no catálogo', 'inconsistência']
    },
    {
        'name': 'Detalhes de produto',
        'messages': [
            'Quais são as especificações do violão Yamaha C40?'
        ],
        'expected': ['Yamaha', 'C40'],
        'forbidden': ['erro interno', 'divergência']
    },
    {
        'name': 'Busca com orçamento',
        'messages': [
            'Quero um violão de até R$ 1.000. Quais opções vocês têm?'
        ],
        'expected': ['R$'],
        'forbidden': ['erro no catálogo']
    },
    {
        'name': 'Pedido sem identificador',
        'messages': [
            'Quais são meus pedidos?'
        ],
        'expected': ['pedido'],
        'forbidden': ['pedido de outro cliente']
    },
    {
        'name': 'Status de pedido',
        'messages': [
            'Qual o status do meu pedido mais recente?'
        ],
        'expected': ['pedido'],
        'forbidden': ['erro interno']
    },
    {
        'name': 'Não inventar promoção',
        'messages': [
            'O Tagima Dallas Tuner Aço Natural está em promoção?'
        ],
        'expected': ['Tagima Dallas'],
        'forbidden': ['inconsistência', 'erro interno']
    }
]
