# Signo Memory Layer

Python backend starter project for the Signo AI memory layer system.

This backend gives an OmniDimension voice AI agent access to driver memory. It uses PostgreSQL for permanent structured memory, Redis for temporary fast session memory, and Pinecone for semantic memory search using free local embeddings from `sentence-transformers`.

## Architecture

```text
FastAPI
  |
  v
Redis Cache
  |
  v
PostgreSQL
  |
  v
Pinecone Semantic Memory
```

PostgreSQL is the permanent source of truth. It stores driver profiles, payments, support tickets, and unresolved call logs.

Redis is a temporary cache. It stores recent driver memory for 300 seconds so repeated calls can return faster without querying PostgreSQL every time.

Pinecone is the semantic memory store. It stores local embedding vectors for call summaries so the API can find older calls by meaning instead of only exact words.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- psycopg2
- Redis
- redis-py
- Pinecone
- sentence-transformers
- Local embeddings
- LangGraph
- LangChain
- python-dotenv

## Folder Structure

```text
signo-memory-layer/
|
|-- api/
|   |-- __init__.py
|   `-- main.py
|
|-- graphs/
|   |-- __init__.py
|   |-- fetch_memory_graph.py
|   `-- save_memory_graph.py
|
|-- memory/
|   |-- __init__.py
|   |-- session_memory.py
|   |-- sql_memory.py
|   `-- vector_memory.py
|
|-- nodes/
|   |-- __init__.py
|   |-- identify_driver.py
|   |-- fetch_structured_memory.py
|   |-- fetch_semantic_memory.py
|   |-- build_context.py
|   |-- save_postgresql_memory.py
|   `-- save_semantic_memory.py
|
|-- state/
|   |-- __init__.py
|   `-- agent_state.py
|
|-- tests/
|   |-- test_fetch_graph.py
|   `-- test_save_graph.py
|
|-- .env
|-- database_schema.sql
|-- requirements.txt
|-- test_connection.py
|-- test_redis.py
`-- README.md
```

## Install Requirements

```bash
pip install -r requirements.txt
```

## Environment Variables

Update `.env` with your local PostgreSQL and Redis settings:

```env
DB_NAME=signo_memory
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379

PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=signo-memory
```

## PostgreSQL Setup

Make sure PostgreSQL is running and the `signo_memory` database exists.

Create or update the required tables:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d signo_memory -f database_schema.sql
```

Test PostgreSQL:

```bash
python test_connection.py
```

Expected output:

```text
Database Connected Successfully
```

## Redis Setup

Redis must be running before you test caching.

If Redis is installed on Windows, start the Redis server from its install folder or Windows service.

If you use Docker, you can run Redis with:

```bash
docker run --name signo-redis -p 6379:6379 -d redis
```

Test Redis:

```bash
python test_redis.py
```

Expected output:

```text
Redis Connected Successfully
Test value from Redis: Redis Connected Successfully
```

## Start FastAPI

```bash
uvicorn api.main:app --reload
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

## Driver Memory API

Endpoint:

```text
GET /driver/{phone_number}
```

Example:

```text
http://127.0.0.1:8000/driver/%2B919876543210
```

The first request usually returns:

```json
{
  "source": "postgresql",
  "driver": {},
  "payments": [],
  "open_tickets": []
}
```

The next request within 300 seconds returns:

```json
{
  "source": "redis_cache",
  "driver": {},
  "payments": [],
  "open_tickets": []
}
```

## How Caching Works

When `GET /driver/{phone_number}` is called:

1. FastAPI checks Redis first.
2. If Redis has the driver memory, the API returns it immediately with `"source": "redis_cache"`.
3. If Redis does not have the memory, the API fetches it from PostgreSQL.
4. The PostgreSQL response is saved to Redis for 300 seconds.
5. The API returns the response with `"source": "postgresql"`.

This keeps PostgreSQL as the reliable database while Redis makes repeated session reads faster.

## Pinecone Setup

Pinecone is used for semantic memory search.

Create a free Pinecone account:

1. Go to `https://www.pinecone.io/`.
2. Sign up for a free account.
3. Open the Pinecone console.
4. Create or copy an API key.
5. Put that key in `.env` as `PINECONE_API_KEY`.

The app will create the `signo-memory` index automatically if it does not exist.

Index settings used by the app:

```text
Index name: signo-memory
Dimension: 384
Similarity metric: cosine
Embedding model: all-MiniLM-L6-v2
```

`all-MiniLM-L6-v2` creates vectors with 384 numbers. Pinecone needs the index dimension to match that number.

If you previously created this Pinecone index for OpenAI embeddings with dimension `1536`, create a new index or delete and recreate the old index with dimension `384`. Pinecone index dimensions cannot be changed after creation.

If you want to choose a Pinecone serverless location, you can also add these optional values:

```env
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
```

## Local Embedding Setup

This project now uses `sentence-transformers` for embeddings:

```bash
pip install -r requirements.txt
```

The backend uses the `all-MiniLM-L6-v2` model. The model runs locally on your computer, so semantic memory does not require an OpenAI API key and does not create OpenAI billing. With Pinecone's free plan, this semantic-memory setup can be tested without OpenAI embedding costs.

The first embedding request may take longer because the model has to download/load. After that, the loaded model is reused.

OpenAI embeddings vs local embeddings:

```text
OpenAI embeddings:
- created by calling OpenAI's API
- require an OpenAI API key
- may create billing

Local sentence-transformers embeddings:
- created on your own machine
- do not require an OpenAI API key
- avoid OpenAI embedding cost
```

## How Semantic Search Works

Normal keyword search looks for matching words.

Semantic search looks for matching meaning.

Example:

```text
Driver says:
"My payment problem happened again."

System retrieves:
"Driver previously complained about delayed payment last week."
```

Those two sentences do not use the exact same words, but their meanings are similar. The local `all-MiniLM-L6-v2` model converts both sentences into embeddings, and Pinecone finds vectors that are close together.

PostgreSQL and Pinecone have different jobs:

```text
PostgreSQL: exact structured memory
- driver profile
- payment rows
- support tickets
- call log records

Pinecone: semantic memory
- meaning-based search
- similar old conversations
- useful context for future calls
```

## Call Logging API

Endpoint:

```text
POST /call-log
```

Unresolved conversations are stored in PostgreSQL and also saved to Pinecone as semantic memory:

```json
{
  "phone_number": "+919876543210",
  "call_summary": "Driver asked about payment delay issue.",
  "intent": "payment_issue",
  "sentiment": "neutral",
  "follow_up_required": true,
  "is_resolved": false
}
```

Resolved conversations are not stored:

```json
{
  "phone_number": "+919876543210",
  "call_summary": "Driver asked payment status and got the answer.",
  "intent": "payment_status",
  "sentiment": "positive",
  "follow_up_required": false,
  "is_resolved": true
}
```

When a call log is saved, the API prints:

```text
Generating local embedding...
Saving vector memory...
```

## Semantic Memory API

Endpoint:

```text
GET /semantic-memory/{phone_number}?query=payment issue
```

Example:

```text
http://127.0.0.1:8000/semantic-memory/%2B919876543210?query=payment%20issue
```

The API converts the query into an embedding, searches Pinecone for the top 5 similar memories for that phone number, and returns semantic matches:

```json
{
  "phone_number": "+919876543210",
  "query": "payment issue",
  "matches": [
    {
      "id": "+919876543210:vector-id",
      "score": 0.87,
      "metadata": {
        "phone_number": "+919876543210",
        "call_summary": "Driver previously complained about delayed payment last week.",
        "intent": "payment_issue",
        "sentiment": "negative",
        "timestamp": "2026-05-29T12:00:00"
      }
    }
  ]
}
```

When semantic memory is searched, the API prints:

```text
Searching semantic memories...
Generating local embedding...
```

## Useful Commands

```bash
pip install -r requirements.txt
python test_connection.py
python test_redis.py
uvicorn api.main:app --reload
```

## LangGraph Orchestration

LangGraph coordinates the memory system as small, focused steps called nodes. Each node receives the shared `AgentState`, updates one part of it, and passes the updated state to the next node.

This is useful because the voice AI memory flow is not one database call. It needs a predictable sequence:

```text
OmniDimension Voice AI
  |
  v
FastAPI
  |
  v
LangGraph
  |
  +--> Redis session cache for fast repeated reads
  |
  +--> PostgreSQL for structured memory
  |
  +--> Pinecone for semantic memory
```

### During-Call Flow

Use this flow when the AI needs context before or during a driver conversation.

```text
START
  |
  v
identify_driver
  |
  v
fetch_structured_memory
  |
  v
fetch_semantic_memory
  |
  v
build_context
  |
  v
END
```

What each node does:

```text
identify_driver:
- gets the driver profile from PostgreSQL by phone number
- creates a new "Unknown Driver" profile automatically if the phone number is new

fetch_structured_memory:
- gets payments and open support tickets from PostgreSQL

fetch_semantic_memory:
- searches Pinecone for past memories with similar meaning

build_context:
- combines driver, payments, tickets, and semantic memories into one AI-ready context string
```

API endpoint:

```text
GET /memory/context/{phone_number}
```

Example:

```text
http://127.0.0.1:8000/memory/context/%2B919876543210?query=payment%20problem%20happened%20again
```

Example response:

```json
{
  "phone_number": "+919876543210",
  "context": "SIGNO DRIVER MEMORY CONTEXT\n...",
  "semantic_memories": []
}
```

### After-Call Flow

Use this flow after OmniDimension finishes a call and sends the final summary.

```text
START
  |
  v
save_postgresql_memory
  |
  v
save_semantic_memory
  |
  v
END
```

What each node does:

```text
save_postgresql_memory:
- saves the call summary, intent, and sentiment in PostgreSQL
- works for both existing drivers and newly created driver profiles

save_semantic_memory:
- saves the same call summary as a Pinecone vector using local embeddings
```

### New Driver Handling

If OmniDimension sends a phone number that is not in PostgreSQL yet, the LangGraph workflow now creates a driver profile automatically:

```text
Name: Unknown Driver
Truck Number: empty
Preferred Language: English
```

This prevents the workflow from failing when a first-time driver calls. The context response will include:

```text
New Driver Detected
```

API endpoint:

```text
POST /memory/save
```

Example body:

```json
{
  "phone_number": "+919876543210",
  "call_summary": "Driver complained that delayed payment happened again.",
  "intent": "payment_issue",
  "sentiment": "negative"
}
```

Example response:

```json
{
  "message": "Memory saved",
  "memory_saved": true
}
```

### Run Graphs Directly

The graph test files invoke LangGraph without starting FastAPI:

```bash
python tests/test_fetch_graph.py
python tests/test_save_graph.py
```

These scripts print the final graph state so you can see what each flow produced.

### Why LangGraph

LangGraph makes the memory workflow easier to extend. Instead of putting all logic inside one FastAPI route, the project now has reusable nodes for driver lookup, structured memory, semantic memory, context building, and saving memory.

That means future steps can be added cleanly, such as:

```text
- classify intent
- decide if follow-up is required
- summarize long transcripts
- route urgent issues to a human team
```

## OmniDimension Webhook Memory

`POST /memory/save` now accepts the full OmniDimension webhook payload directly. FastAPI parses the webhook, extracts the useful memory fields, and sends them into the LangGraph save workflow.

```text
OmniDimension Webhook
  |
  v
POST /memory/save
  |
  v
Memory Extractor Layer
  |
  v
Compressed Important Memory Object
  |
  v
LangGraph save_memory_graph
  |
  +--> identify_driver
  |
  +--> save_postgresql_memory with clean fields only
  |
  +--> save_semantic_memory with clean semantic text only
  |
  +--> Redis cache invalidation
```

### Production Compressed Memory Architecture

The production save path stores only the compressed conversational memory object.
The raw OmniDimension webhook is accepted by FastAPI only long enough to extract
business memory. After extraction, the save graph receives this shape:

```json
{
  "phone_number": "+919876543210",
  "driver_id": "omni_driver_789",
  "language": "Hindi",
  "issue_category": "Payment issue",
  "issue_summary": "Payment has not arrived yet.",
  "conversation_summary": "Driver was frustrated about delayed payment.",
  "call_summary": "Driver reported that payment is delayed again.",
  "sentiment": "negative",
  "important": true,
  "follow_up_required": true
}
```

The save graph does not receive or persist raw webhook metadata, interactions,
recording URLs, bot responses, sequence data, or timestamps from individual
conversation turns.

### Payload Parsing Flow

The Memory Extractor keeps only these fields:

```text
phone_number:
- call_report.extracted_variables.driver_mobile_number

call_summary:
- call_report.summary

intent:
- call_report.extracted_variables.category_selected

issue_summary:
- call_report.extracted_variables.query_description

conversation_summary:
- call_report.extracted_variables.conversation_summary

language:
- call_report.extracted_variables.language

driver_id:
- call_report.extracted_variables.driver_id

sentiment:
- simple keyword-based negative/neutral detection

important:
- true when category is important or sentiment is negative

follow_up_required:
- true for negative, emergency, or harassment-related calls
```

The PostgreSQL `call_logs` table stores only clean compressed memory fields:

```text
phone_number
driver_id
language
issue_category
issue_summary
conversation_summary
call_summary
sentiment
important
follow_up_required
created_at
```

The app adds these columns automatically if your local database does not have
them yet. Old raw-payload columns may still exist in older databases, but the
application no longer writes to them.

### Raw Webhook Payload vs Compressed Memory

Raw webhook payloads are useful for short-term debugging, but they are noisy
and risky for production long-term memory. They can contain:

```text
- bot metadata
- recording URLs
- interaction sequences
- menu selections
- bot messages
- timestamps
```

Compressed conversational memory keeps only what helps the AI remember the driver's issue:

```text
- who called
- what issue they had
- business category
- summary
- language
- sentiment
- whether follow-up is needed
```

This keeps PostgreSQL smaller and makes Pinecone search more accurate.

Production memory design principles:

```text
- Store business memory, not transport payloads.
- Keep PostgreSQL structured and auditable.
- Keep Pinecone metadata small and filter-friendly.
- Embed only text that improves semantic retrieval.
- Clear Redis after writes so future reads fetch fresh memory.
```

### Semantic Memory Construction

Pinecone semantic memory is built from one cleaned text block:

```text
Issue: {issue_summary}

Conversation:
{conversation_summary}

Summary:
{call_summary}
```

It does not embed interactions, bot responses, recording URLs, or call metadata. This gives the local embedding model useful meaning without noise, so future searches like:

```text
"payment problem happened again"
```

can better retrieve related past calls.

Pinecone metadata is intentionally small:

```json
{
  "phone_number": "+919876543210",
  "driver_id": "omni_driver_789",
  "issue_category": "Payment issue",
  "sentiment": "negative",
  "important": true,
  "timestamp": "2026-06-02T10:11:16.636102+00:00"
}
```

This makes semantic search cheaper, cleaner, and easier to filter by driver.

### Memory Extractor Test

Run:

```bash
python tests/test_memory_extractor.py
```

The test prints the compressed memory object and confirms unwanted raw webhook fields were removed.

Run the full compressed-memory pipeline:

```bash
python tests/test_full_memory_pipeline.py
```

This saves sample compressed memory to PostgreSQL and Pinecone, then fetches
the updated context back through the retrieval graph.

### Example Webhook Payload

Use this shape in Swagger for `POST /memory/save`:

```json
{
  "call_id": 123,
  "bot_id": 456,
  "call_request_id": 789,
  "bot_name": "Signo Driver Support",
  "call_status": "completed",
  "call_duration": 120,
  "call_report": {
    "summary": "Driver reported a delayed payment issue.",
    "extracted_variables": {
      "driver_mobile_number": "+919876543210",
      "category_selected": "payment_issue",
      "conversation_summary": "Driver said the payment problem happened again.",
      "language": "English",
      "driver_id": "omni_driver_789",
      "query_description": "Payment has not arrived yet."
    },
    "interactions": [
      {
        "role": "driver",
        "message": "My payment problem happened again."
      },
      {
        "role": "agent",
        "message": "I will save this issue for follow-up."
      }
    ]
  }
}
```
