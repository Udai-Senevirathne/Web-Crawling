# 🕷️ Web Crawler Chatbot

> **A fully functional RAG-based web crawler that scrapes websites and answers questions about the crawled content.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat&logo=react&logoColor=black)](https://reactjs.org)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🕷️ **Web Crawler** | Crawls websites using Playwright with configurable depth & page limits |
| 🧠 **RAG Pipeline** | Splits text into chunks, generates embeddings, stores in vector database |
| 💬 **Chat Interface** | Clean chat UI with source attribution |
| ⚙️ **Admin Panel** | Web-based content ingestion interface |
| 🚀 **Zero Cost** | Groq LLM (free) + local embeddings + ChromaDB (local) |
| 📁 **File Upload** | Support for PDF and text file ingestion |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **[Groq API Key](https://console.groq.com)** (free)

### Installation

```bash
# Clone the repository
git clone https://github.com/Udai-Senevirathne/Web-Crawling.git
cd Web-Crawling

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

Edit the `.env` file in the root directory:

```env
# Required: Get your free API key from https://console.groq.com
GROQ_API_KEY=your_groq_api_key_here

# Vector Store (default: local ChromaDB)
VECTOR_STORE_TYPE=chroma
CHROMA_PERSIST_DIRECTORY=./data/chroma_db

# Database (optional - uses in-memory by default)
USE_FAKE_DB=1
```

### Run the Application

**Terminal 1 - Backend:**
```powershell
# Windows
.\.venv\Scripts\Activate.ps1
python run_uvicorn.py

# Linux/Mac
source .venv/bin/activate
python run_uvicorn.py
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

### Access

| Service | URL | Description |
|---------|-----|-------------|
| 💬 **Chat UI** | http://localhost:5173 | Main chat interface |
| ⚙️ **Admin Panel** | Click Admin button in UI | Crawl websites and ingest content |
| 📚 **API Docs** | http://localhost:8000/docs | Swagger documentation |

---

## 📁 Project Structure

```
Web-Crawling/
├── .env                      # API keys & configuration
├── requirements.txt          # Python dependencies
├── run_uvicorn.py            # Windows-compatible server runner
│
├── backend/                  # 🔙 PYTHON BACKEND
│   ├── api/
│   │   ├── main.py           # FastAPI app entry point
│   │   └── routes/
│   │       ├── chat.py       # POST /api/chat
│   │       ├── health.py     # GET /api/health
│   │       └── ingestion.py  # POST /api/ingest
│   ├── services/
│   │   ├── chatbot_orchestrator.py  # RAG pipeline
│   │   ├── llm_service.py           # Groq/OpenAI integration
│   │   ├── embeddings.py            # Local embeddings
│   │   └── vector_store.py          # ChromaDB/Pinecone
│   └── data_ingestion/
│       ├── scraper.py        # Playwright web crawler
│       ├── chunker.py        # Text splitter
│       └── pipeline.py       # Ingestion orchestrator
│
├── frontend/                 # 🎨 REACT FRONTEND
│   └── src/
│       ├── App.tsx           # Main app
│       └── components/
│           ├── ClientChat.tsx    # Chat interface
│           └── AdminPanel.tsx    # Ingestion UI
│
└── data/
    └── chroma_db/            # 💾 Local vector storage
```

---

## 🔄 How It Works

### 1. Ingestion Phase (Crawl a website)
```
Website URL
    ↓
┌─────────────────┐
│    SCRAPER      │  Playwright visits pages, extracts HTML
└────────┬────────┘
         ↓
┌─────────────────┐
│    CHUNKER      │  Splits text into ~1000 char chunks
└────────┬────────┘
         ↓
┌─────────────────┐
│   EMBEDDINGS    │  Converts each chunk to 384-dim vector
└────────┬────────┘
         ↓
┌─────────────────┐
│  VECTOR STORE   │  Stores vectors in ChromaDB
└─────────────────┘
```

### 2. Query Phase (Ask a question)
```
User Question: "What is your pricing?"
    ↓
┌─────────────────┐
│   EMBEDDINGS    │  Convert question to vector
└────────┬────────┘
         ↓
┌─────────────────┐
│  VECTOR SEARCH  │  Find top 5 most similar chunks
└────────┬────────┘
         ↓
┌─────────────────┐
│      LLM        │  Generate response using context + question
└────────┬────────┘
         ↓
"Based on the website, pricing starts at $9/month..."
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send message & get AI response |
| `GET` | `/api/chat/stats` | Get system statistics |
| `POST` | `/api/ingest` | Start website crawl |
| `GET` | `/api/ingest/{job_id}` | Check crawl status |
| `GET` | `/api/health` | Health check |

### Example: Start Crawling

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://docs.python.org", "max_pages": 10, "max_depth": 2}'
```

### Example: Chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is this website about?"}'
```

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Frontend** | React 18 + TypeScript + Vite |
| **Backend** | FastAPI + Python 3.10 |
| **LLM** | Groq (Llama 3.3 70B) - Free tier |
| **Embeddings** | Sentence Transformers (local) |
| **Vector DB** | ChromaDB (local) |
| **Web Scraping** | Playwright + BeautifulSoup |

---

## 💰 Cost

| Component | Cost |
|-----------|------|
| LLM (Groq) | **$0** (free tier) |
| Embeddings | **$0** (local) |
| Vector DB | **$0** (local) |
| **Total** | **$0/month** |

---

## 🔧 Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | `groq`, `openai`, or `google` | `groq` |
| `GROQ_API_KEY` | Your Groq API key | Required |
| `VECTOR_STORE_TYPE` | `chroma` or `pinecone` | `chroma` |
| `USE_FAKE_DB` | Use in-memory DB (no MongoDB) | `1` |
| `TOP_K` | Chunks to retrieve | `5` |
| `CHUNK_SIZE` | Characters per chunk | `1000` |

---

## 🧪 CLI Usage

You can also run the crawler from command line:

```bash
# Crawl a website
python -m backend.data_ingestion.pipeline --url https://example.com --max-pages 20

# With reset (clear existing data)
python -m backend.data_ingestion.pipeline --url https://example.com --reset
```

---

## 📝 License

MIT License - Free to use and modify.

---

## 👤 Author

**Udai Senevirathne**  
GitHub: [@Udai-Senevirathne](https://github.com/Udai-Senevirathne)
