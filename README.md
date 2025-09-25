# RAG-based BCI Literature Scout

A lightweight RAG demo that retrieves recent BCI/Neurotech papers and produces concise, evidence-backed trend summaries with clickable citations and reproducible query snapshots.

## 🚀 Features

- **Provenance-first summaries** — every claim has a clickable citation and confidence score
- **Trend timeline visualization** — papers per year, top keywords over time
- **Claim-level evidence** extraction — supporting sentences from papers
- **Interactive cluster explorer** — hover to see keywords and representative papers
- **Reproducibility snapshot** — QR/JSON encoding for result reproduction
- **Conservative assistant mode** — explicit listing of uncertain findings
- **Export-ready notes** — BibTeX + TL;DR bullets for email outreach

## 🛠 Tech Stack

- **Frontend**: React + TypeScript + Tailwind CSS (CDN)
- **Backend**: FastAPI + Python
- **Vector Store**: FAISS
- **Embeddings**: SentenceTransformers
- **LLM**: Gemini for summarization
- **Data Sources**: arXiv, PubMed, Semantic Scholar APIs

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- npm

## 🚀 Quick Start

### Backend Setup

1. **Clone and setup environment**:
   ```bash
   git clone <repository-url>
   cd rag_bci
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp backend/env.example backend/.env
   # Edit backend/.env with your API keys
   ```

4. **Run the backend**:
   ```bash
   cd backend
   python main.py
   ```

   Backend will be available at `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your API URL
   ```

3. **Run the frontend**:
   ```bash
   npm run dev
   ```

   Frontend will be available at `http://localhost:5173`

## 📁 Project Structure

```
rag_bci/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main application
│   ├── config.py           # Configuration settings
│   ├── models.py           # Pydantic models
│   └── env.example         # Environment template
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   ├── types/          # TypeScript types
│   │   └── utils/          # Utility functions
│   └── env.example         # Environment template
├── data/                   # Data storage (created at runtime)
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔧 Development

### Backend Development

- **Linting**: `flake8 backend/`
- **Formatting**: `black backend/`
- **Type checking**: `mypy backend/`
- **Testing**: `pytest backend/tests/`

### Frontend Development

- **Linting**: `npm run lint`
- **Type checking**: `npm run type-check`
- **Build**: `npm run build`

## 📊 API Endpoints

- `GET /` - Root endpoint (health check)
- `GET /health` - Health check
- `POST /query` - Main literature search endpoint (Sprint 3)

## 🎯 Development Timeline

- **Sprint 1**: ✅ Project Foundation & Core Infrastructure
- **Sprint 2**: Data Pipeline & Vector Store Setup
- **Sprint 3**: RAG Engine & LLM Integration
- **Sprint 4**: Basic Frontend & Search Interface
- **Sprint 5**: Advanced Features & Visualizations
- **Sprint 6**: Polish, Testing & Demo Preparation

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For questions or issues, please open a GitHub issue.
