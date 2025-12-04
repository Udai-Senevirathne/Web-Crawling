# RAG Web Crawler Chatbot - Architecture Overview

A **Retrieval-Augmented Generation (RAG)** chatbot that crawls websites and answers questions based on the crawled content.

---

## 🎯 What This Project Does

1. **Admin enters a website URL** → System crawls and indexes the content
2. **User asks a question** → System searches indexed content and generates an AI response
3. **Response includes sources** → Users can verify where the information came from

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│  ┌─────────────────┐              ┌─────────────────────────┐   │
│  │   Client Chat   │              │      Admin Panel        │   │
│  │  - Ask questions│              │  - Enter URL to crawl   │   │
│  │  - View sources │              │  - Monitor progress     │   │
│  └────────┬────────┘              └───────────┬─────────────┘   │
└───────────┼───────────────────────────────────┼─────────────────┘
            │                                   │
            ▼                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Chat Route  │  │Health Route │  │   Ingestion Route       │  │
│  │ /api/chat   │  │ /api/health │  │   /api/ingest           │  │
│  └──────┬──────┘  └─────────────┘  └───────────┬─────────────┘  │
│         │                                      │                 │
│         ▼                                      ▼                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  SERVICES LAYER                           │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │   │
│  │  │ LLM Service │ │  Embedding  │ │   Vector Store      │ │   │
│  │  │   (Groq)    │ │  (Local)    │ │   (ChromaDB)        │ │   │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                DATA INGESTION PIPELINE                    │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │   │
│  │  │  Scraper    │ │  Chunker    │ │   Embeddings        │ │   │
│  │  │ (Playwright)│→│ (Text Split)│→│   (Vectorize)       │ │   │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Frontend
| Technology | Purpose | Why We Use It |
|------------|---------|---------------|
| **React 18** | UI Framework | Component-based, declarative UI with hooks |
| **TypeScript** | Language | Type safety, better developer experience |
| **Vite** | Build Tool | Fast HMR, modern ES modules, quick builds |
| **CSS3** | Styling | Custom professional theme (Teal/Slate) |

### Backend
| Technology | Purpose | Why We Use It |
|------------|---------|---------------|
| **FastAPI** | Web Framework | Async support, automatic OpenAPI docs, fast |
| **Python 3.11+** | Language | Rich ML/AI ecosystem, easy to read |
| **Pydantic** | Validation | Data validation and serialization |
| **Uvicorn** | ASGI Server | High-performance async server |

### AI/ML Services
| Technology | Purpose | Why We Use It |
|------------|---------|---------------|
| **Groq** | LLM Provider | Free tier, fast inference (Llama 3.3 70B) |
| **Sentence Transformers** | Embeddings | Local, free, no API limits |
| **ChromaDB** | Vector Database | Simple, embedded, persistent storage |

### Web Scraping
| Technology | Purpose | Why We Use It |
|------------|---------|---------------|
| **Playwright** | Browser Automation | Handles JavaScript-rendered pages |
| **BeautifulSoup** | HTML Parsing | Extract text content from HTML |

---

## 📁 Project Structure

```
SLT/
│
├── 📄 .env                           # API keys & configuration
├── 📄 .gitignore                     # Git ignore rules
├── 📄 README.md                      # Project overview
├── 📄 ARCHITECTURE.md                # This file
├── 📄 requirements.txt               # Python dependencies
│
├── 🔙 backend/                       # ══════ PYTHON BACKEND ══════
│   │
│   ├── 🌐 api/                       # HTTP Layer (REST API)
│   │   ├── main.py                   #   → FastAPI app setup & CORS
│   │   └── routes/
│   │       ├── chat.py               #   → POST /api/chat (send message)
│   │       ├── health.py             #   → GET /api/health (status check)
│   │       └── ingestion.py          #   → POST /api/ingest (crawl website)
│   │
│   ├── 🧠 services/                  # Business Logic Layer
│   │   ├── chatbot_orchestrator.py   #   → Combines all services for chat
│   │   ├── llm_service.py            #   → Groq/OpenAI LLM integration
│   │   ├── embeddings.py             #   → Text → Vector conversion
│   │   └── vector_store.py           #   → ChromaDB read/write
│   │
│   ├── 🕷️ data_ingestion/            # Web Scraping Pipeline
│   │   ├── scraper.py                #   → Playwright browser automation
│   │   ├── chunker.py                #   → Split text into chunks
│   │   └── pipeline.py               #   → Orchestrate: scrape→chunk→embed→store
│   │
│   └── ⚙️ utils/                      # Utilities
│       ├── config.py                 #   → Environment variable management
│       └── logger.py                 #   → Logging configuration
│
├── 🎨 frontend/                      # ══════ REACT FRONTEND ══════
│   │
│   ├── 📄 index.html                 # HTML entry point
│   ├── 📄 package.json               # NPM dependencies
│   ├── 📄 vite.config.ts             # Vite build configuration
│   ├── 📄 tsconfig.json              # TypeScript configuration
│   │
│   └── src/
│       ├── 📄 main.tsx               # React entry point
│       ├── 📄 App.tsx                # Main app with routing & auth
│       ├── 📄 App.css                # Global styles & admin modal
│       │
│       ├── 🧩 components/
│       │   ├── ClientChat.tsx        #   → User chat interface
│       │   ├── ClientChat.css        #   → Chat styling
│       │   ├── AdminPanel.tsx        #   → Admin URL ingestion UI
│       │   └── AdminPanel.css        #   → Admin styling
│       │
│       └── 🔌 services/
│           └── api.ts                #   → Backend API client
│
├── 💾 data/                          # ══════ DATA STORAGE ══════
│   └── chroma_db/                    # Vector database files
│       └── chroma.sqlite3            #   → Persistent embeddings
│
└── 🧪 tests/                         # ══════ UNIT TESTS ══════
    ├── conftest.py                   # Pytest fixtures
    └── test_basic.py                 # Basic tests
```

---

## 🔗 How Files Connect

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER REQUEST                               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  frontend/src/components/ClientChat.tsx                              │
│  └── Captures user input, displays messages                         │
└─────────────────────────────────────────────────────────────────────┘
                                  │ calls
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  frontend/src/services/api.ts                                        │
│  └── sendMessage() → POST http://localhost:8000/api/chat            │
└─────────────────────────────────────────────────────────────────────┘
                                  │ HTTP
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  backend/api/routes/chat.py                                          │
│  └── @router.post("/chat") → Validates request                      │
└─────────────────────────────────────────────────────────────────────┘
                                  │ calls
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  backend/services/chatbot_orchestrator.py                            │
│  └── process_message() → Coordinates the RAG pipeline               │
└─────────────────────────────────────────────────────────────────────┘
                    │                               │
          ┌────────┴────────┐             ┌────────┴────────┐
          ▼                 ▼             ▼                 ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ embeddings.py    │ │ vector_store.py  │ │ llm_service.py   │
│ └── Embed query  │ │ └── Search DB    │ │ └── Generate     │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## 🔄 How RAG Works

### 1. Ingestion Phase (Admin crawls a website)
```
Website URL
    ↓
┌─────────────────┐
│    SCRAPER      │  Playwright visits pages, extracts HTML
└────────┬────────┘
         ↓
┌─────────────────┐
│    CHUNKER      │  Splits text into ~1000 char chunks with overlap
└────────┬────────┘
         ↓
┌─────────────────┐
│   EMBEDDINGS    │  Converts each chunk to 384-dim vector
└────────┬────────┘
         ↓
┌─────────────────┐
│  VECTOR STORE   │  Stores vectors in ChromaDB for fast search
└─────────────────┘
```

### 2. Query Phase (User asks a question)
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

## 💰 Cost Analysis

| Component | Provider | Cost |
|-----------|----------|------|
| LLM (Chat) | Groq | **$0** (free tier) |
| Embeddings | Local | **$0** (runs on your machine) |
| Vector DB | ChromaDB | **$0** (local file storage) |
| **Total** | | **$0/month** |

---

## 🔧 Configuration (.env)

```env
# LLM Provider
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.3-70b-versatile

# Vector Store
CHROMA_PERSIST_DIRECTORY=./data/chroma_db

# RAG Settings
TOP_K=5              # Number of chunks to retrieve
CHUNK_SIZE=1000      # Characters per chunk
CHUNK_OVERLAP=200    # Overlap between chunks
```

---

## 🚀 Running the Project

### Start Backend
```powershell
cd D:\Personal\SLT
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

### Start Frontend
```powershell
cd D:\Personal\SLT\frontend
npm run dev
```

### Access
- **Chat UI**: http://localhost:3000
- **Admin Panel**: Click ⚙️ icon, password: `admin123`
- **API Docs**: http://localhost:8000/docs

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/chat/stats` | Get system statistics |
| POST | `/api/chat` | Send message, get AI response |
| POST | `/api/ingest` | Start web crawling job |
| GET | `/api/ingest/{job_id}` | Check crawling job status |

---

## 🎨 UI Design

- **Color Scheme**: Teal (#0d9488) + Slate (#0f172a)
- **Font**: Inter (Google Fonts)
- **Style**: Modern, professional, dark theme
- **Layout**: Full-screen chat with floating admin button

---

## 🔮 Future Improvements

1. **Authentication** - Proper user/admin login system
2. **Multiple Knowledge Bases** - Support different websites
3. **Streaming Responses** - Real-time token streaming
4. **File Upload** - Support PDF/DOC ingestion
5. **Analytics** - Track popular questions
6. **Caching** - Cache frequent queries

---

## 📝 License

MIT License - Free to use and modify.
