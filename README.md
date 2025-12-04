# 🤖 RAG Web Crawler Chatbot

> **A production-ready Retrieval-Augmented Generation chatbot that learns from any website.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat&logo=react&logoColor=black)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6?style=flat&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🕷️ **Web Crawler** | Automatically scrapes and indexes any website using Playwright |
| 🧠 **RAG Pipeline** | Retrieval-Augmented Generation for accurate, contextual answers |
| 💬 **Modern Chat UI** | Clean, responsive interface with real-time messaging |
| ⚙️ **Admin Panel** | Easy-to-use dashboard for content management |
| 🚀 **Zero Cost** | Uses Groq (free) + local embeddings — $0/month |
| 📱 **Responsive** | Works seamlessly on desktop and mobile |

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React + TS    │────▶│    FastAPI      │────▶│    ChromaDB     │
│   (Frontend)    │◀────│    (Backend)    │◀────│  (Vector Store) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
             ┌─────────────┐       ┌─────────────┐
             │    Groq     │       │   Local     │
             │ (LLM - Free)│       │ Embeddings  │
             └─────────────┘       └─────────────┘
```

> 📖 See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.

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
# LLM Configuration
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama-3.3-70b-versatile

# Vector Store
CHROMA_PERSIST_DIRECTORY=./data/chroma_db

# RAG Settings
TOP_K=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Run the Application

**Terminal 1 - Backend:**
```bash
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Access

| Service | URL |
|---------|-----|
| 💬 Chat UI | http://localhost:3000 |
| ⚙️ Admin Panel | Click ⚙️ icon → Password: `admin123` |
| 📚 API Docs | http://localhost:8000/docs |

---

## 📁 Project Structure

```
slt-chatbot/
├── backend/
│   ├── api/              # REST API endpoints
│   │   └── routes/       # chat, health, ingestion
│   ├── services/         # LLM, embeddings, vector store
│   ├── data_ingestion/   # Web scraping pipeline
│   └── utils/            # Config & logging
├── frontend/
│   └── src/
│       ├── components/   # ClientChat, AdminPanel
│       └── services/     # API client
├── data/
│   └── chroma_db/        # Vector database
├── .env                  # Configuration
└── requirements.txt      # Python dependencies
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

| Category | Technology | Why? |
|----------|------------|------|
| **Frontend** | React 18, TypeScript, Vite | Fast, type-safe, modern DX |
| **Backend** | FastAPI, Python 3.11 | Async, auto-docs, fast |
| **LLM** | Groq (Llama 3.3 70B) | Free, fast inference |
| **Embeddings** | Sentence Transformers | Local, no API costs |
| **Vector DB** | ChromaDB | Simple, embedded, fast |
| **Scraping** | Playwright, BeautifulSoup | JS rendering support |

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

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | `groq` \| `openai` \| `google` | `groq` |
| `GROQ_API_KEY` | Your Groq API key | — |
| `GROQ_MODEL` | Model to use | `llama-3.3-70b-versatile` |
| `TOP_K` | Chunks to retrieve | `5` |
| `CHUNK_SIZE` | Chars per chunk | `1000` |
| `CHUNK_OVERLAP` | Overlap between chunks | `200` |
| `CORS_ORIGINS` | Allowed origins | `localhost:3000,8000` |

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

## 📈 Roadmap

- [ ] 🔐 User authentication system
- [ ] 📊 Analytics dashboard
- [ ] 🔄 Streaming responses
- [ ] 📎 File upload (PDF, DOCX)
- [ ] 🌐 Multi-language support
- [ ] 💾 Conversation history persistence

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Groq](https://groq.com) — Free, fast LLM inference
- [ChromaDB](https://trychroma.com) — Simple vector database
- [FastAPI](https://fastapi.tiangolo.com) — Modern Python web framework
- [Sentence Transformers](https://sbert.net) — State-of-the-art embeddings

---

<p align="center">
  <sub>Built with ❤️ using Python & React</sub>
</p>

