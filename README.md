# 🤖 RAG Web Crawler Chatbot

> **A production-ready Retrieval-Augmented Generation chatbot that learns from any website.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat&logo=react&logoColor=black)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6?style=flat&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Repository:** [Udai-Senevirathne/Web-Crawling](https://github.com/Udai-Senevirathne/Web-Crawling)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🕷️ **Web Crawler** | Crawls websites using Playwright with configurable depth & page limits |
| 🧠 **RAG Pipeline** | Chunks text, generates embeddings, stores in ChromaDB for semantic search |
| 💬 **Client Chat** | Clean, professional chat interface with source attribution |
| ⚙️ **Admin Panel** | Password-protected dashboard to add content sources |
| 🚀 **Zero Cost** | Groq LLM (free) + local sentence-transformers embeddings |
| 🎨 **Modern UI** | Teal/Slate dark theme with Inter font, fully responsive |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + TypeScript)                │
│  ┌─────────────────────┐              ┌─────────────────────────┐   │
│  │    ClientChat.tsx   │              │     AdminPanel.tsx      │   │
│  │  • Send messages    │              │  • Enter URL to crawl   │   │
│  │  • Display sources  │              │  • Set page limit/depth │   │
│  │  • Conversation     │              │  • View system stats    │   │
│  └──────────┬──────────┘              └───────────┬─────────────┘   │
└─────────────┼─────────────────────────────────────┼─────────────────┘
              │              HTTP API               │
              ▼                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         BACKEND (FastAPI + Python)                   │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │ /api/chat   │  │  /api/health    │  │    /api/ingest          │  │
│  │ POST message│  │  GET status     │  │  POST start crawl       │  │
│  └──────┬──────┘  └─────────────────┘  └───────────┬─────────────┘  │
│         │                                          │                 │
│         ▼                                          ▼                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              CHATBOT ORCHESTRATOR                             │   │
│  │  1. Embed query → 2. Search ChromaDB → 3. Generate response  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│         │                    │                     │                 │
│         ▼                    ▼                     ▼                 │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────────┐  │
│  │ LLM Service │    │  Vector Store   │    │ Embedding Service   │  │
│  │ Groq API    │    │  ChromaDB       │    │ all-MiniLM-L6-v2    │  │
│  │ Llama 3.3   │    │  Local Storage  │    │ Local (384 dim)     │  │
│  └─────────────┘    └─────────────────┘    └─────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │               DATA INGESTION PIPELINE                         │   │
│  │  Scraper (Playwright) → Chunker (1000 chars) → Embeddings    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

> 📖 See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed file-by-file documentation.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **[Groq API Key](https://console.groq.com)** (free)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/slt-chatbot.git
cd slt-chatbot

# Create & activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### Configuration

Create a `.env` file in the root directory:

```env
# LLM Configuration (Using Groq - Free)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Embeddings (Local - No API needed)
EMBEDDING_PROVIDER=local

# Vector Store
CHROMA_PERSIST_DIRECTORY=./data/chroma_db

# RAG Settings
TOP_K=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Run the Application

**Terminal 1 - Backend:**
```powershell
# Windows
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

### Access

| Service | URL | Description |
|---------|-----|-------------|
| 💬 **Chat UI** | http://localhost:3000 | Main chat interface |
| ⚙️ **Admin Panel** | Click ⚙️ → Password: `admin123` | Add content sources |
| 📚 **API Docs** | http://localhost:8000/docs | Swagger documentation |

---

## 📁 Project Structure

```
Web-Crawling/
├── .env                      # API keys & configuration
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── ARCHITECTURE.md           # Detailed architecture docs
│
├── backend/                  # 🔙 PYTHON BACKEND
│   ├── api/
│   │   ├── main.py           # FastAPI app entry point
│   │   └── routes/
│   │       ├── chat.py       # POST /api/chat
│   │       ├── health.py     # GET /api/health
│   │       └── ingestion.py  # POST /api/ingest
│   ├── services/
│   │   ├── chatbot_orchestrator.py  # RAG coordinator
│   │   ├── llm_service.py           # Groq/OpenAI integration
│   │   ├── embeddings.py            # Local embeddings
│   │   └── vector_store.py          # ChromaDB operations
│   ├── data_ingestion/
│   │   ├── scraper.py        # Playwright web crawler
│   │   ├── chunker.py        # Text splitter
│   │   └── pipeline.py       # Ingestion orchestrator
│   └── utils/
│       ├── config.py         # Environment config
│       └── logger.py         # Logging setup
│
├── frontend/                 # 🎨 REACT FRONTEND
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx           # Main app + routing
│       ├── App.css           # Global styles
│       ├── components/
│       │   ├── ClientChat.tsx/css   # Chat interface
│       │   └── AdminPanel.tsx/css   # Admin UI
│       └── services/
│           └── api.ts        # Backend API client
│
├── data/
│   └── chroma_db/            # 💾 Vector database storage
│
└── tests/                    # 🧪 Unit tests
    ├── conftest.py
    └── test_basic.py
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/chat/stats` | System statistics |
| `POST` | `/api/chat` | Send message & get response |
| `POST` | `/api/ingest` | Start website crawl |
| `GET` | `/api/ingest/{id}` | Check crawl status |

<details>
<summary><b>📝 Example Request</b></summary>

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What services do you offer?",
    "conversation_id": "user-123"
  }'
```

**Response:**
```json
{
  "response": "Based on the website content, we offer...",
  "sources": [
    {"url": "https://example.com/services", "title": "Our Services"}
  ],
  "conversation_id": "user-123"
}
```
</details>

---

## 🛠️ Tech Stack

| Category | Technology | Details |
|----------|------------|---------|
| **Frontend** | React 18 + TypeScript | Vite build, modern hooks |
| **Styling** | CSS3 | Teal (#0d9488) / Slate (#0f172a) theme, Inter font |
| **Backend** | FastAPI + Python 3.11 | Async, auto-generated OpenAPI docs |
| **LLM** | Groq | Llama 3.3 70B - Free tier, fast inference |
| **Embeddings** | Sentence Transformers | all-MiniLM-L6-v2 (local, 384 dimensions) |
| **Vector DB** | ChromaDB | Embedded, persistent, SQLite-based |
| **Web Scraping** | Playwright + BeautifulSoup | JavaScript rendering support |

---

## 💰 Cost Breakdown

| Component | Provider | Cost |
|-----------|----------|------|
| LLM Inference | Groq Free Tier | **$0** |
| Embeddings | Local (all-MiniLM-L6-v2) | **$0** |
| Vector Storage | ChromaDB (Local) | **$0** |
| **Total Monthly Cost** | | **$0** |

---

## 🔧 Configuration Options

| Variable | Description | Default | Implemented |
|----------|-------------|---------|-------------|
| `LLM_PROVIDER` | `groq` \| `openai` \| `google` | `groq` | ✅ |
| `GROQ_API_KEY` | Your Groq API key | — | ✅ |
| `GROQ_MODEL` | Model to use | `llama-3.3-70b-versatile` | ✅ |
| `EMBEDDING_PROVIDER` | `local` \| `google` \| `openai` | `local` | ✅ |
| `TOP_K` | Chunks to retrieve | `5` | ✅ |
| `CHUNK_SIZE` | Chars per chunk | `1000` | ✅ |
| `CHUNK_OVERLAP` | Overlap between chunks | `200` | ✅ |
| `CORS_ORIGINS` | Allowed origins | `localhost:3000,8000` | ✅ |
| `CHROMA_PERSIST_DIRECTORY` | Vector DB path | `./data/chroma_db` | ✅ |

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test
pytest tests/test_basic.py -v
```

---

## 🚢 Deployment

### Option 1: Manual

```bash
# Build frontend
cd frontend && npm run build

# Run with production settings
ENVIRONMENT=production python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

### Option 2: Docker

```bash
docker build -t rag-chatbot .
docker run -p 8000:8000 --env-file .env rag-chatbot
```

---

## 📈 What's Implemented

### ✅ Completed Features
- [x] **Web Crawler** — Playwright-based with configurable depth/pages
- [x] **Text Chunking** — 1000 char chunks with 200 char overlap
- [x] **Local Embeddings** — Sentence Transformers (no API cost)
- [x] **Vector Storage** — ChromaDB with persistent storage
- [x] **LLM Integration** — Groq (Llama 3.3 70B) for responses
- [x] **Chat API** — POST /api/chat with conversation history
- [x] **Ingestion API** — Async job-based crawling
- [x] **Client Chat UI** — Professional dark theme
- [x] **Admin Panel** — Password-protected (admin123)
- [x] **Source Attribution** — Shows where answers come from
- [x] **Error Handling** — Graceful error messages in UI

### 🔮 Future Improvements
- [ ] User authentication system
- [ ] Streaming responses (SSE)
- [ ] File upload (PDF, DOCX)
- [ ] Conversation persistence
- [ ] Analytics dashboard
- [ ] Multi-language support

---

## 👤 Author

**Udai Senevirathne**  
GitHub: [@Udai-Senevirathne](https://github.com/Udai-Senevirathne)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Groq](https://groq.com) — Free, ultra-fast LLM inference
- [ChromaDB](https://trychroma.com) — Simple embedded vector database
- [FastAPI](https://fastapi.tiangolo.com) — Modern Python web framework
- [Sentence Transformers](https://sbert.net) — State-of-the-art embeddings
- [Playwright](https://playwright.dev) — Reliable browser automation

---

<p align="center">
  <sub>Built with ❤️ by Udai Senevirathne</sub>
</p>

