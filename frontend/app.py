
import os

import httpx
import streamlit as st

API_URL = os.getenv('API_URL', 'http://127.0.0.1:8000')

st.set_page_config(
    page_title='Empório da Música',
    page_icon='🎸',
    layout='centered'
)

st.markdown('''
<style>
    .block-container {
        max-width: 900px;
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
</style>
''', unsafe_allow_html=True)

def request(method: str, path: str, customer_id: int, data: dict | None = None):
    with httpx.Client(timeout=15) as client:
        response = client.request(
            method,
            f'{API_URL}{path}',
            headers={'X-Customer-ID': str(customer_id)},
            json=data
        )
        response.raise_for_status()
        return response.json()

@st.cache_data(show_spinner=False)
def load_customers():
    with httpx.Client(timeout=15) as client:
        response = client.get(f'{API_URL}/customers')
        response.raise_for_status()
        return response.json()

def start_session(customer_id: int):
    session = request('POST', '/sessions', customer_id)
    return session['id']

def change_customer():
    st.session_state.customer_id = st.session_state.selected_customer
    st.session_state.session_id = None

try:
    customers = load_customers()
except httpx.HTTPError as exc:
    st.error(f'Não foi possível carregar os clientes: {exc}')
    st.stop()

if not customers:
    st.error('Nenhum cliente cadastrado.')
    st.stop()

customers_by_id = {customer['customer_id']: customer for customer in customers}
customer_ids = list(customers_by_id)

if 'customer_id' not in st.session_state or st.session_state.customer_id not in customers_by_id:
    st.session_state.customer_id = customer_ids[0]

if 'session_id' not in st.session_state:
    st.session_state.session_id = None

with st.sidebar:
    st.subheader('Cliente de teste')

    st.selectbox(
        'Selecione o cliente',
        options=customer_ids,
        format_func=lambda customer_id: customers_by_id[customer_id]['name'],
        index=customer_ids.index(st.session_state.customer_id),
        key='selected_customer',
        on_change=change_customer
    )

    st.caption('Identificação simulada para demonstração.')

if st.session_state.session_id is None:
    try:
        st.session_state.session_id = start_session(st.session_state.customer_id)
    except httpx.HTTPError as exc:
        st.error(f'Não foi possível iniciar a sessão: {exc}')
        st.stop()

st.title('🎸 Empório da Música')
st.caption('Seu assistente virtual para instrumentos musicais')

@st.fragment(run_every='2s')
def chat_history():
    session_id = st.session_state.session_id
    customer_id = st.session_state.customer_id

    try:
        messages = request(
            'GET',
            f'/sessions/{session_id}/messages',
            customer_id
        )
    except httpx.HTTPError as exc:
        st.error(f'Erro ao consultar mensagens: {exc}')
        return

    if not messages:
        st.info('Olá! Como posso ajudar você hoje?')

    for message in messages:
        role = 'user' if message['role'] == 'user' else 'assistant'

        with st.chat_message(role):
            st.markdown(message['content'])

    if messages and messages[-1]['role'] == 'user':
        with st.chat_message('assistant'):
            st.write('⏳ Preparando resposta...')

chat_history()

prompt = st.chat_input('Digite sua mensagem...')

if prompt:
    try:
        request(
            'POST',
            f'/sessions/{st.session_state.session_id}/messages',
            st.session_state.customer_id,
            {'content': prompt}
        )
        st.rerun()
    except httpx.HTTPError as exc:
        st.error(f'Erro ao enviar mensagem: {exc}')
