import asyncio

from langchain_core.messages import AIMessage, HumanMessage

from backend.agent.agent import agent
from backend.agent.context import AgentContext
from backend.database import close_db, init_db
from tests.agent_cases import AGENT_CASES

CUSTOMER_ID = 10

async def run_case(case):
    messages = []

    for question in case['messages']:
        messages.append(HumanMessage(content=question))

        result = await agent.ainvoke(
            {'messages': messages},
            context=AgentContext(customer_id=CUSTOMER_ID),
            config={'recursion_limit': 20}
        )

        response = result['messages'][-1]

        if not isinstance(response, AIMessage):
            raise ValueError('Resposta inválida do agente')

        answer = response.text
        messages.append(AIMessage(content=answer))

    answer_lower = answer.lower()

    missing = [
        value for value in case['expected']
        if value.lower() not in answer_lower
    ]

    forbidden = [
        value for value in case['forbidden']
        if value.lower() in answer_lower
    ]

    passed = not missing and not forbidden

    print(f'\n{"PASS" if passed else "FAIL"} | {case["name"]}')
    print(f'Pergunta: {case["messages"][-1]}')
    print(f'Resposta: {answer}')

    if missing:
        print(f'Esperado e ausente: {missing}')

    if forbidden:
        print(f'Conteúdo proibido encontrado: {forbidden}')

    return passed

async def main():
    await init_db()

    try:
        results = []

        for case in AGENT_CASES:
            try:
                results.append(await run_case(case))
            except Exception as exc:
                print(f'\nERROR | {case["name"]}: {exc}')
                results.append(False)

        passed = sum(results)

        print(f'\nResultado: {passed}/{len(results)} testes aprovados')
    finally:
        await close_db()

if __name__ == '__main__':
    asyncio.run(main())
