# Empório da Música — AI Agent

A conversational customer-support agent for **Empório da Música**, a fictional musical-instrument store based in Campo Grande, Brazil.

The agent answers questions about the product catalog, pricing, stock availability, orders, and store policies. It maintains conversational context and calls dedicated tools to retrieve operational data rather than relying solely on the language model's knowledge.

## Features

- Customer support in Brazilian Portuguese, with concise, context-aware answers.
- Product-category browsing and product search by description, characteristics, price, and availability.
- Product details and active promotion lookup.
- Order history and status lookup for the selected customer.
- Answers grounded in structured store policies covering payment, shipping, returns, warranty, and support.
- Persistent conversation history in PostgreSQL.
- Streamlit chat UI with a demo-customer selector and automatic message refresh.
- Asynchronous message processing with persistent tasks, scheduling, recovery, and retries.

## Architecture

```text
Streamlit (customer chat UI)
         |
         v
FastAPI (sessions and messages)
         |
         v
PostgreSQL (customers, products, orders, conversations, tasks)
         |
         v
Async worker (task processing)
         |
         v
LangChain Agent + OpenAI
         |
         +-- list_categories / search_products / get_product
         +-- get_my_orders / get_order
         +-- get_policy
         |
         v
PostgreSQL + pgvector (semantic product search)
```

The API receives and persists incoming messages. An **asynchronous worker** runs the agent and stores its responses, while the frontend periodically polls for updates. This avoids keeping HTTP requests open throughout generation and allows failed tasks to be retried.

### Technical decisions

| Area | Choice |
|---|---|
| Language | **Python 3.12**. |
| Agent framework | **LangChain `create_agent`** with tool calling. The LLM decides when to consult products, orders, or store policies. |
| Model and provider | **OpenAI API**, with a model selected through environment configuration. |
| Retrieval | **Embeddings + pgvector** with cosine similarity for descriptive queries; structured SQL filters for category, price, and availability. |
| User interface | **Streamlit**, providing a usable chat experience with minimal frontend complexity. |
| API | **FastAPI**, separating the UI from backend operations and exposing session and message endpoints. |
| Persistence | **PostgreSQL + Tortoise ORM** for business data, sessions, messages, and processing tasks. |
| Background execution | **Async worker** with persisted, scheduled tasks and retry/recovery handling. |
| Policies | **Structured JSON**, derived from store policy material and queried by topic instead of sending a complete policy document to the LLM on every request. |

### Product retrieval

The product catalog is imported from the CSV files located at /data. An indexing process builds searchable text for each product, generates an embedding, and saves it in PostgreSQL. A content hash and model-version identifier allow unchanged products to be skipped during subsequent indexing runs.

The `search_products` tool supports two modes:

- **Semantic search:** when a query describes a product, brand, use case, or preference, the system embeds the query and ranks matching products by cosine similarity.
- **Structured search:** when no free-text query is supplied, the system applies database filters and sorts products by price.

Filters can also be combined with semantic search. Similarity indicates relevance, not guaranteed attribute matching; retrieved attributes must be checked before a recommendation is made. The `get_product` tool provides complete details when needed.

The project does not implement hybrid full-text retrieval or give the agent unrestricted SQL access. Database operations are encapsulated in narrowly scoped tools with explicit parameters.

### Prompting and tool strategy

The system prompt defines the assistant's persona, response language, concise style, and restrictions against inventing prices, inventory, order information, or commercial terms. Tool descriptions define when each operation should be used and how to interpret its arguments and returned data.

Available tools:

- `list_categories`: retrieve product categories.
- `search_products`: search and filter products, with pagination.
- `get_product`: retrieve product specifications and active promotions.
- `get_my_orders`: list orders belonging to the current customer.
- `get_order`: retrieve details of an order belonging to the current customer.
- `get_policy`: retrieve store information and policies by topic.

The backend passes the customer identifier through the tool's trusted execution context; the model does not select an arbitrary customer ID when accessing orders. Policies are retrieved on demand to keep context focused and avoid relying on the model's general knowledge for store-specific rules.

## Requirements

- **Python 3.12**.
- [uv](https://docs.astral.sh/uv/) for dependency management and command execution.
- [Docker](https://www.docker.com/) with Docker Compose for PostgreSQL and pgvector.
- An **OpenAI API key** with access to the configured models.

## Setup and execution

Run the following commands from the **project root**. API, worker, and frontend should run in separate terminals.

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure environment variables

Create a `.env` file in the project root with the following configuration:

```dotenv
# Database
DATABASE_URL=postgres://emporio:emporio_dev@127.0.0.1:5433/emporio
TEST_DATABASE_URL=postgres://emporio:emporio_dev@127.0.0.1:5433/emporio_test

# Language Model
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-6-luna
LLM_API_KEY=YOUR_OPENAI_API_KEY

# Embeddings
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1024
```

The database URLs point to the PostgreSQL instance started through Docker Compose, exposed on port `5433`.

The main database stores application data, while the test database isolates automated tests.

Replace `YOUR_OPENAI_API_KEY` with a valid OpenAI API key. The language model can be changed through `LLM_MODEL`, provided the selected model is supported by the configured provider.

### 3. Start the database

```bash
docker compose up -d
```

The development Docker configuration exposes PostgreSQL on **port 5433** on the host and **5432** inside the container.

### 4. Apply database migrations

```bash
uv run tortoise migrate
```

### 5. Import data and build the semantic index

```bash
uv run python -m scripts.import_data
uv run python -m backend.search.indexing
```

### 6. Start the API

**Terminal 1:**

```bash
uv run fastapi dev backend/main.py
```

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 7. Start the worker

**Terminal 2:**

```bash
uv run python -m backend.worker
```

The worker polls pending tasks, processes messages through the agent, and stores replies.

### 8. Launch the chat UI

**Terminal 3:**

```bash
uv run streamlit run frontend/app.py
```

Open `http://localhost:8501`, select a demo customer by name, and start chatting. Customer selection is simulated identification, not production-grade authentication.

## Tests

### Automated backend tests

```bash
uv run python -m tests.run
```

The test runner uses a separate test database and executes the automated suite.

### Agent behavior checks

```bash
uv run python -m tests.check_agent
```

These checks invoke the actual LLM and cover product discovery, conversational context, payment and return policies, customer orders, and promotions.

In the latest manual development run, 13 of 13 agent cases passed. These checks assert expected and disallowed expressions; they are not exhaustive verification of prices, stock levels, or policy correctness against the database.

## Example Conversations

Five reproducible conversation scenarios are available in the
[`examples/`](examples/) directory.

The examples demonstrate:

1. Product discovery using semantic search and price filters.
2. Multi-turn conversations with contextual understanding.
3. Payment methods, installments, and promotional rules.
4. Customer-specific order retrieval and status queries.
5. Return policies and online purchase withdrawal rules.

To regenerate the conversations:

```bash
uv run python -m tests.demo_agent
```

The script runs the agent against the configured database and
saves the resulting conversations as Markdown files.

## Known limitations and future improvements

- **Demo-only identity selection:** the UI lets evaluators switch customers, but a production application would require authentication, authorization, and API-level access controls.
- **Incomplete policy coverage:** the structured policies do not necessarily capture every business exception or legal scenario.
- **Semantic retrieval limitations:** similar products can be retrieved without satisfying every requested attribute. Potential improvements include richer structured filters, hybrid search, and formal retrieval evaluation.
- **Model costs and latency:** generation and indexing depend on external APIs; costs vary with the model, tool calls, and context length. Token accounting and observability can be expanded.
- **Operational robustness:** task persistence and retries provide basic resilience, not full production monitoring, tracing, or deployment guarantees.
- **Evaluation coverage:** the behavior cases are samples, not universal correctness guarantees. Future tests should verify structured facts and policy rules deterministically and assess security and retrieval quality.

## AI-assisted development

**ChatGPT** and **Codex** were used to discuss architecture, review code, investigate errors, and design test scenarios. Suggestions were integrated incrementally and checked in the development environment.