# VeriCite: Fact-Checking & Citation-Attributed RAG System

A robust, production-grade, zero-dependency-overhead Document-Based RAG System named **VeriCite** built from scratch in Python. It includes a page-aware markdown preprocessing and ingestion pipeline, semantic vector databases integration (local ChromaDB), multi-format parsers (PDF, DOCX, TXT, MD), dynamic similarity filters, OpenAI GPT-4o LLM integration with complete attribution, and a breathtaking, high-fidelity responsive dark-mode Single Page Web Application!

---

## 🌌 Key Highlights & Features

1. **Intelligent Multi-Format Ingestion Pipeline**
   - Page-boundary preserving parsing of **PDF**, **DOCX**, **TXT**, and **Markdown** files.
   - Restores layout and styles, converting all text directly into uniform Markdown.
   - Encodes specific `<!-- PAGE: X -->` markers into the document stream for exact citation tracking.

2. **Semantic Text Chunking**
   - Employs a recursive text-splitter with chunk size and overlap limits.
   - Highly accurate, page-aware block segmentation.
   - Complete metadata enrichment (filename, page offsets, timestamp index, size details).

3. **Hybrid Embeddings & Local Fallbacks**
   - Default integration with OpenAI's premium `text-embedding-3-small` model.
   - Automatic local offline fallback utilizing a **deterministic word-level hashing vectorizer** scaled to 1536 dimensions. This enables zero-key local testing that actually maintains basic semantic query matching!

4. **Self-Contained Persistent Vector Storage**
   - High-performance cosine similarity searches powered by an embedded local ChromaDB instance.
   - Self-cleaning index layers: automatically purges old records when re-uploading documents.

5. **LLM Citation Orchestration**
   - Direct prompt inject layer ensuring the LLM synthesizes structured markdown answers using *only* the retrieved context blocks.
   - Enforces bracketed inline citations: `[Source: document.pdf, page X]`.
   - Incorporates a **highly detailed mock summarization engine** when running without OpenAI keys, making it 100% testable out of the box.

6. **Breathtaking Dark-Mode SPA Console**
   - Self-contained, zero-npm-dependency frontend using Google Fonts, premium animated iconography, glassmorphic layouts, and floating ambient glow spheres.
   - Features dynamic upload drag-and-drop slots with visual progress bars.
   - Contains an interactive conversation box: **citations are clickable**, scrolling/highlighting corresponding document fragments instantly!

---

## 📂 Directory Layout

```
VeriCite/
├─ backend/
│   ├─ src/
│   │   ├─ loaders/             # multi-format loaders (base, pdf, docx, txt, md)
│   │   ├─ chunker/             # recursive page-aware segmentation
│   │   ├─ embedder/            # OpenAI & deterministically hashed mock embedder
│   │   ├─ vectordb/            # local persistent ChromaDB wrapper
│   │   ├─ retriever/           # similarity filter searches
│   │   ├─ llm/                 # GPT prompt layout & offline mock engines
│   │   ├─ config.py            # env loads (.env support)
│   │   ├─ exceptions.py        # unified custom exceptions
│   │   ├─ orchestrator.py      # pipeline flow glue
│   │   └─ api.py               # REST API endpoints (FastAPI)
│   ├─ scripts/
│   │   └─ demo.py              # interactive CLI demo
│   └─ requirements.txt         # backend package registry
├─ frontend/
│   ├─ src/
│   │   ├─ components/          # modular React components (Uploader, List, Console)
│   │   ├─ App.jsx              # central coordinate state orchestrator
│   │   └─ index.css            # premium responsive CSS design
│   ├─ index.html               # main Vite mount page
│   ├─ package.json             # frontend dependencies config
│   ├─ vite.config.js           # Vite development server settings
│   └─ Dockerfile               # multi-stage builder & Nginx serving container
├─ docker-compose.yml           # multi-container docker orchestration
└─ README.md                    # system handbook
```

---

## 🛠️ Quick Start & Setup

### Option 1: Quick Start Local Installation

#### 1. Setup Virtual Environment & Install Dependencies
First, set up your Python 3 environment in your workspace terminal:
```bash
cd /home/ankushraut/DayUsers/ankushraut/Official/Projects/GIT/VeriCite
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### 2. Configure Environment variables
Create a `.env` file under the `/home/ankushraut/DayUsers/ankushraut/Official/Projects/GIT/VeriCite/backend/` directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o
CHROMA_DB_PATH=./data/chroma_db
LOG_LEVEL=INFO
PORT=8080
HOST=0.0.0.0
```
*Note: If no `OPENAI_API_KEY` is supplied, the system automatically falls back to offline mock mode for both embeddings and LLM responses, allowing you to try the system instantly!*

#### 3. Run the End-to-End CLI Demo
Execute the demo script. It automatically generates a sample document in `./data/vericite_spec.md`, ingests it into the Chroma DB instance, queries it, prints the cited answers, matches attributed sources, and displays total execution metrics:
```bash
python backend/scripts/demo.py
```

To run it on a specific document with your own custom query:
```bash
python backend/scripts/demo.py --file /path/to/your/document.pdf --query "Summarize the conclusion."
```

#### 4. Spin Up the FastAPI Web API Server
To start the REST API server:
```bash
python -m uvicorn backend.src.api:app --reload --host 0.0.0.0 --port 8080
```
Confirm the API is online by navigating to: `http://localhost:8080/api/health`

#### 5. Launch the Front-End Console
Since the front-end has **zero build dependencies**, you can run it immediately!
Simply open `frontend/index.html` in your web browser, or serve it using any lightweight server:
```bash
# Using python HTTP server
cd frontend
python3 -m http.server 3000
```
Open `http://localhost:3000` to interact with the premium QA Console!

---

## 🐳 Option 2: Docker Compose Orchestration

A multi-stage `docker-compose.yml` has been included in the root directory, enabling you to build and spin up the complete application stack (Backend API + Front-End HTTP Server) with a single command!

### Start the Services
```bash
docker compose up --build
```
This boots up:
- The FastAPI API server listening at `http://localhost:8080`.
- The premium Front-End QA Web Console listening at `http://localhost:3000`.

---

## 🧪 Automated Testing

A complete suite of modular testing scripts is located in `backend/tests/` verifying loaders, custom metadata tracking, chunking behaviors, vector stores, and unified orchestration.
To execute all test configurations:
```bash
pytest backend/
```

---

## 🤖 Model Context Protocol (MCP) Server Integration

This repository includes a native, production-grade **Model Context Protocol (MCP)** server built on top of the VeriCite system core. The MCP server allows AI models and assistant clients (such as **Claude Desktop**, **Cursor**, or autonomous agents) to directly interact with your local document index as a semantic search and ingestion tool.

### 🛠️ Exposed Tools

The MCP server exposes four rich tools to connected models:
1. **`query_rag`**: Submit a semantic query to retrieve document contexts and get a citation-attributed synthesized answer from the local database.
2. **`list_documents`**: Returns a list of all currently ingested and indexed source documents with file size and max page counts.
3. **`ingest_document`**: Index a new local document file (PDF, TXT, DOCX, MD) on the fly, immediately adding its semantic embeddings to the database index.
4. **`delete_document`**: Wipes all semantic vectors and clean physical storage entries for a selected file.

### 🚀 Setup & Launch Guide

#### 1. Install local dependencies
Ensure the local virtual environment has all necessary dependencies (including the newly added `mcp` SDK) installed:
```bash
# Activate your local virtual environment
source venv/bin/activate
pip install -r backend/requirements.txt
```

#### 2. Run the MCP Server locally
The MCP server uses the high-performance **Stdio** transport layer. You can launch it with:
```bash
python -m backend.src.mcp_server
```

#### 3. Integrate with Claude Desktop
To expose these local document search capabilities to your Claude Desktop client, add the following configuration block under `mcpServers` in your Claude configuration file:

* **File Path (Linux/Ubuntu):** `~/.config/Claude/claude_desktop_config.json`
* **File Path (macOS):** `~/Library/Application Support/Claude/claude_desktop_config.json`
* **File Path (Windows):** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "local-document-vericite": {
      "command": "/home/ankushraut/DayUsers/ankushraut/Official/Projects/GIT/VeriCite/venv/bin/python",
      "args": [
        "-m",
        "backend.src.mcp_server"
      ],
      "env": {
        "OPENAI_API_KEY": "YOUR_OPENAI_API_KEY_HERE",
        "CHROMA_DB_PATH": "/home/ankushraut/DayUsers/ankushraut/Official/Projects/GIT/VeriCite/backend/data/chroma_db"
      }
    }
  }
}
```

Restart Claude Desktop, and you will see a new 🔌 plug icon! You can now ask Claude questions like:
* *"Search my local document VeriCite index for..."*
* *"What documents are currently ingested in my local database?"*
* *"Please index the text document at `/path/to/notes.txt`"*

