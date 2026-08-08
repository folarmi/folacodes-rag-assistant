# Folacodes RAG Assistant

Folacodes RAG Assistant is an internal knowledge assistant that uses Retrieval-Augmented Generation (RAG) to answer questions about company policies, procedures, forms, and internal guides.

## Features

- Natural language question answering
- Semantic search over company documents
- Source attribution
- Conversation history
- User feedback collection
- Hallucination reduction through RAG

## Technology Stack

- Python
- Flask
- ChromaDB
- FastEmbed
- Groq (Llama 3.3 70B)
- Docker
- GitHub Actions
- Render

## Project Structure

```text
app/
documents/
evaluation/
scripts/
tests/
vectorstore/
```

## Setup Instructions

### Clone the repository

```bash
git clone <repository-url>
cd folacodes-rag-assistant
```

### Create a virtual environment

```bash
python -m venv .venv
```

### Activate the environment

Mac/Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file:

```env
GROQ_API_KEY=your_api_key

DOCUMENTS_PATH=documents
VECTORSTORE_PATH=vectorstore/chroma_db

EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

TOP_K=4
PORT=5001
```

### Build the vector database

```bash
python scripts/ingest.py
```

### Run locally

```bash
flask --app app.app:create_app run --port 5001
```

Open:

```
http://localhost:5001
```

## Running Tests

```bash
pytest -v
```

## Docker

Build:

```bash
docker compose build
```

Run:

```bash
docker compose up
```

## Deployment

Live application:

https://folacodes-rag-assistant.onrender.com

Health endpoint:

https://folacodes-rag-assistant.onrender.com/api/health
