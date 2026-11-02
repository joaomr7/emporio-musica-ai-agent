import asyncio
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage

from backend.agent.agent import agent
from backend.agent.context import AgentContext
from backend.database import close_db, init_db

OUTPUT_DIR = Path('examples')
CUSTOMER_ID = 5

SCENARIOS = [
    {
        'name': '01_product_search',
        'title': 'Product Search',
        'questions': [
            'Quais opções de violões disponíveis custam até R$ 1.000?',
            'Qual desses você recomenda para um iniciante?'
        ]
    },
    {
        'name': '02_conversation_context',
        'title': 'Conversation Context',
        'questions': [
            'Quais marcas de baterias vocês trabalham?',
            'Quais são os modelos disponíveis?'
        ]
    },
    {
        'name': '03_payment_policies',
        'title': 'Payment Policies',
        'questions': [
            'É possível parcelar uma compra?',
            'E pagando no PIX, tenho desconto?',
            'Posso acumular o desconto com uma promoção?'
        ]
    },
    {
        'name': '04_customer_orders',
        'title': 'Customer Orders',
        'questions': [
            'Quais são meus pedidos?',
            'Qual o status do meu pedido mais recente?'
        ]
    },
    {
        'name': '05_returns_policy',
        'title': 'Returns Policy',
        'questions': [
            'Comprei um instrumento pela internet e me arrependi. Posso devolver?',
            'E se o instrumento apresentar defeito?'
        ]
    }
]

async def run_scenario(scenario):
    messages = []
    lines = [
        f'# {scenario["title"]}',
        '',
        f'Customer: Demo customer (ID {CUSTOMER_ID})',
        ''
    ]

    for question in scenario['questions']:
        messages.append(HumanMessage(content=question))

        result = await agent.ainvoke(
            {'messages': messages},
            context=AgentContext(customer_id=CUSTOMER_ID),
            config={'recursion_limit': 20}
        )

        response = result['messages'][-1]

        if not isinstance(response, AIMessage):
            raise ValueError('The agent did not return a valid response')

        answer = response.text

        if not answer.strip():
            raise ValueError('The agent returned an empty response')

        messages.append(AIMessage(content=answer))

        lines.extend([
            '## Customer',
            '',
            question,
            '',
            '## Assistant',
            '',
            answer,
            ''
        ])

        print(f'  Customer: {question}')
        print(f'  Assistant: {answer}\n')

    output_path = OUTPUT_DIR / f'{scenario["name"]}.md'
    output_path.write_text('\n'.join(lines), encoding='utf-8')

    print(f'Saved: {output_path}\n')

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    await init_db()

    try:
        for scenario in [SCENARIOS[4]]:
            print(f'\n=== {scenario["title"]} ===')

            try:
                await run_scenario(scenario)
            except Exception as exc:
                print(f'ERROR: {scenario["name"]}: {exc}')
    finally:
        await close_db()

if __name__ == '__main__':
    asyncio.run(main())
