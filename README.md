# VeriCite

## 1. Project Overview

**Project Name:** VeriCite
**Project Type:** Full Stack (FastAPI backend + React frontend + MCP server)
**Status:** Development

### Description

VeriCite is a document-based RAG (retrieval-augmented generation) system built from scratch in Python for fact-checking and citation-attributed question answering. It ingests PDF, DOCX, TXT, and Markdown documents through a page-aware preprocessing pipeline, stores embeddings in a local ChromaDB vector store, and uses an LLM to synthesize answers with inline citations (`[Source: document.pdf, page X]`) pointing back to the exact source page. It includes a FastAPI backend, a dependency-free React/Vite frontend, an MCP server for AI assistant integration, and Docker Compose orchestration.

## 2. Core Features

- Multi-format ingestion pipeline: page-boundary-preserving parsing of PDF, DOCX, TXT, and Markdown into uniform Markdown with embedded page markers for citation tracking.
- Semantic chunking: recursive, page-aware text splitting with configurable chunk size/overlap and metadata enrichment (filename, page offsets, timestamps).
- Hybrid embeddings: uses OpenAI's `text-embedding-3-small` by default. When no `OPENAI_API_KEY` is set, it automatically falls back to a deterministic word-hashing vectorizer (1536 dimensions) so the system is usable offline without any API key.
- Persistent vector storage via local ChromaDB, with cosine similarity search and automatic cleanup of stale records on re-upload.
- LLM citation orchestration: prompts GPT-4o to answer strictly from retrieved context with enforced bracketed citations. When no `OPENAI_API_KEY` is set, falls back to a rule-based mock summarization engine instead of a real LLM call, so the system is fully testable without credentials.
- Dependency-free dark-mode SPA frontend with drag-and-drop upload, clickable citations that scroll to and highlight the source fragment.
- MCP (Model Context Protocol) server exposing `query_rag`, `list_documents`, `ingest_document`, and `delete_document` tools for integration with Claude Desktop, Cursor, or other MCP-aware clients.

## 3. Tech Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Vector store | ChromaDB (local, persistent) |
| LLM / Embeddings | OpenAI API (embeddings + GPT-4o), with an offline mock fallback for both |
| Frontend | React (via Vite), plain CSS, no external UI framework |
| Integration | MCP SDK (Model Context Protocol server) |
| Deployment | Docker, Docker Compose, Nginx (frontend container) |
| Testing | pytest |

## 4. Project Structure

```
VeriCite/
├── backend/
│   ├── src/
│   │   ├── loaders/       # multi-format loaders (pdf, docx, txt, md)
│   │   ├── chunker/        # recursive page-aware segmentation
│   │   ├── embedder/       # OpenAI embedder + offline hashing fallback
│   │   ├── vectordb/       # ChromaDB wrapper
│   │   ├── retriever/      # similarity search
│   │   ├── llm/            # GPT prompt layer + offline mock engine
│   │   ├── orchestrator.py # pipeline glue
│   │   ├── api.py          # FastAPI REST endpoints
│   │   └── mcp_server.py   # MCP server exposing RAG tools
│   ├── scripts/demo.py     # interactive CLI demo
│   ├── tests/test_vericite.py
│   └── requirements.txt
├── frontend/
│   ├── src/                # React components, App.jsx, index.css
│   ├── index.html
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## 5. Prerequisites

- Python 3.x with `venv`
- Node/npm only needed if rebuilding the frontend (it otherwise runs as static files)
- Docker and Docker Compose (optional, for containerized run)
- An OpenAI API key (optional — the system runs fully offline with mock embeddings/LLM if omitted)

## 6. How to Run

### Local development

Set up the backend environment:

```bash
cd VeriCite
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

Create a `.env` file under `backend/` (see [Environment Variables](#8-environment-variables) below). If `OPENAI_API_KEY` is omitted, the system runs entirely offline using the mock embedder and mock summarization engine described above.

Run the interactive CLI demo (ingests a sample document, queries it, prints cited answers):

```bash
python backend/scripts/demo.py
# or against your own file:
python backend/scripts/demo.py --file /path/to/your/document.pdf --query "Summarize the conclusion."
```

Start the API server:

```bash
python -m uvicorn backend.src.api:app --reload --host 0.0.0.0 --port 8080
```

Check health at `http://localhost:8080/api/health`.

Serve the frontend (no build step required):

```bash
cd frontend
python3 -m http.server 3000
```

Open `http://localhost:3000`.

### Docker

```bash
docker compose up --build
```

This starts the FastAPI backend on `http://localhost:8080` and the frontend on `http://localhost:3000`.

### MCP server

```bash
source venv/bin/activate
pip install -r backend/requirements.txt
python -m backend.src.mcp_server
```

To connect from Claude Desktop, add an entry under `mcpServers` in the Claude Desktop config file (`~/.config/Claude/claude_desktop_config.json` on Linux, `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "local-document-vericite": {
      "command": "/path/to/VeriCite/venv/bin/python",
      "args": ["-m", "backend.src.mcp_server"],
      "env": {
        "OPENAI_API_KEY": "YOUR_OPENAI_API_KEY_HERE",
        "CHROMA_DB_PATH": "/path/to/VeriCite/backend/data/chroma_db"
      }
    }
  }
}
```

## 7. API Documentation

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/upload` | Ingest a document (PDF/DOCX/TXT/MD) |
| POST | `/api/query` | Ask a question; returns an answer with inline source citations |
| GET | `/api/documents` | List ingested documents |
| DELETE | `/api/documents/{filename}` | Remove a document and its vectors |

## 8. Environment Variables

```env
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o
CHROMA_DB_PATH=./data/chroma_db
LOG_LEVEL=INFO
PORT=8080
HOST=0.0.0.0
```

All variables are optional; without `OPENAI_API_KEY` the system substitutes the offline mock embedder and mock summarization engine noted in Core Features.

## 9. Testing

```bash
pytest backend/
```

Tests live in `backend/tests/test_vericite.py`.

## 10. Known Limitations

- Without an `OPENAI_API_KEY`, answers are generated by a rule-based mock summarizer, not a real LLM — useful for offline testing but not representative of production answer quality.
- Vector storage is a local, file-based ChromaDB instance; there is no multi-user or distributed deployment story.

## 11. License

No `LICENSE` file is present in this repository.
