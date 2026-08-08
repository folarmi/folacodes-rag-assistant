# Design and Evaluation

# 1. Design and Architecture Decisions

## Architecture

The application follows a Retrieval-Augmented Generation (RAG) architecture.

Flow:

```text
Documents
    ↓
Chunking
    ↓
Embeddings
    ↓
ChromaDB
    ↓
User Question
    ↓
Similarity Search
    ↓
LLM Response
```

The system retrieves relevant document chunks and passes them to the language model to generate grounded answers.

---

## Technology Choices

### Flask

Flask was selected because it is lightweight and easy to integrate with AI libraries.

### ChromaDB

ChromaDB was selected as the vector database because it supports efficient similarity search and local persistence.

### FastEmbed

FastEmbed was selected because it is lightweight and suitable for deployment on limited hardware resources.

### Groq

Groq was selected because it provides fast inference with the Llama 3.3 language model.

### Docker

Docker was used to ensure portability and consistent deployment.

### GitHub Actions

GitHub Actions was used for automated testing and continuous integration.

---

# 2. Evaluation

## Evaluation Approach

The system was evaluated using three categories of questions:

### Policy questions

Examples:

- How many annual leave days do employees receive?
- How do employees submit expense claims?

Expected outcome:

The system should retrieve the correct document and provide an accurate answer.

---

### Knowledge-base questions

Examples:

- How do I request new software?
- How do I reset my password?

Expected outcome:

The system should retrieve the correct guide.

---

### Out-of-scope questions

Examples:

- Who won the FIFA World Cup in 2022?
- What is the capital of France?

Expected outcome:

The system should refuse to answer because the information is not available in the knowledge base.

---

## Results

The system successfully:

- Retrieved relevant document chunks.
- Generated grounded answers.
- Displayed source documents.
- Refused unrelated questions.
- Stored user feedback and chat history.

---

## Testing Results

Automated testing results:

- 30 tests passed successfully.
- Docker build completed successfully.
- GitHub Actions pipeline passed.
- Deployment to Render was successful.
