import asyncio

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from backend.agent.agent import agent
from backend.agent.context import AgentContext
from backend.database import close_db, init_db

from backend.models import Product

async def main():
    await init_db()

    try:
        scenarios = [
            'Quais violões disponíveis custam até R$ 1000?',
            'Quais são as características do Yamaha C40?',
            'Vocês aceitam PIX?',
            'Quais são meus pedidos?',
            'Qual o status do meu pedido 1?',
            'Posso devolver uma compra online?'
        ]

        for question in scenarios:
            result = await agent.ainvoke(
                {'messages': [HumanMessage(content=question)]},
                context=AgentContext(customer_id=3),
                config={'recursion_limit': 10}
            )

            print(f'\nQuestion: {question}')
            print(f'Response: {result["messages"][-1].content}')

            for message in result['messages']:
                if isinstance(message, AIMessage) and message.tool_calls:
                    for call in message.tool_calls:
                        print(f'Tool: {call["name"]}')
                        print(f'Arguments: {call["args"]}')

                elif isinstance(message, ToolMessage):
                    print(f'Result: {message.content}')

    finally:
        await close_db()

if __name__ == '__main__':
    asyncio.run(main())
