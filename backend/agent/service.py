from langchain_core.messages import AIMessage, HumanMessage

from backend.agent.agent import agent
from backend.agent.context import AgentContext
from backend.models import Message, Session

async def process_conversation(session_id: int, task_id: int) -> str:
    session = await Session.get(id=session_id)

    task_messages = await Message.filter(
        session_id=session_id,
        task_id=task_id,
        role='user'
    ).order_by('id')

    if not task_messages:
        raise ValueError('Task without user messages')

    last_message_id = task_messages[-1].id

    history = await Message.filter(
        session_id=session_id,
        id__lte=last_message_id
    ).order_by('id')

    messages = []

    for message in history:
        if message.role == 'user':
            messages.append(HumanMessage(content=message.content))
        elif message.role == 'assistant':
            messages.append(AIMessage(content=message.content))

    result = await agent.ainvoke(
        {'messages': messages},
        context=AgentContext(customer_id=session.customer_id),
        config={'recursion_limit': 20}
    )

    response = result['messages'][-1]

    if not isinstance(response, AIMessage):
        raise ValueError('The agent did not return a valid message')

    content = response.text

    if not content.strip():
        raise ValueError('The agent returned an empty response')

    return content