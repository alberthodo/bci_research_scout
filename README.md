# BCI Research Scout

A powerful AI-powered research tool that helps Brain-Computer Interface (BCI) researchers discover, analyze, and synthesize the latest scientific literature. Built with modern RAG (Retrieval-Augmented Generation) technology, it provides evidence-backed insights with clickable citations and confidence scores.

## 🌟 Features

### 🔍 **Intelligent Literature Search**
- **Real-time paper fetching** from arXiv, PubMed, and Semantic Scholar
- **Smart query enhancement** with BCI-specific context
- **Parallel API processing** for faster results
- **Intelligent caching** to reduce search times from 60s to 2-4s

### 📊 **AI-Powered Analysis**
- **Evidence-backed claims** with confidence scores and citations
- **Trend summarization** using Google Gemini LLM
- **Automatic keyword extraction** and relevance scoring
- **Reproducible research snapshots** for academic integrity

### 🎨 **Modern Interface**
- **Google-style search experience** with dynamic UI transitions
- **Clean, responsive design** built with React and Tailwind CSS
- **Real-time loading states** and error handling
- **Export-ready results** for research workflows

### ⚡ **Performance Optimized**
- **Redis caching** with in-memory fallback
- **Background paper pre-fetching** for popular BCI topics
- **Query similarity detection** to avoid redundant processing
- **LLM response caching** for faster repeated queries

## 🛠 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **FAISS** - Efficient vector similarity search
- **SentenceTransformers** - State-of-the-art embeddings
- **Google Gemini** - Advanced LLM for summarization
- **Redis** - High-performance caching (with in-memory fallback)

### Frontend
- **React 18** - Modern UI library
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Vite** - Fast build tool and dev server

### Data Sources
- **arXiv** - Preprint repository
- **PubMed** - Biomedical literature
- **Semantic Scholar** - AI-powered research tool

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/bci_research_scout.git
cd bci_research_scout
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys (see Configuration section)
```

### 3. Frontend Setup
```bash
cd frontend
npm install

# Configure environment
cp .env.example .env
# Edit .env with your backend URL (default: http://localhost:8000)
```

### 4. Run the Application
```bash
# Terminal 1: Start backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev
```

Visit `http://localhost:5173` to use the application!

## ⚙️ Configuration

### Required API Keys
Create a `backend/.env` file with the following:

```env
# Google Gemini API (required for AI summarization)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Redis configuration (defaults to localhost:6379)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

### Getting API Keys
1. **Google Gemini**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey) to get your free API key
2. **Redis** (optional): Install Redis locally or use a cloud service like Redis Cloud

## 📁 Project Structure

```
bci_research_scout/
├── backend/                    # FastAPI backend
│   ├── main.py                # Main application entry point
│   ├── config.py              # Configuration settings
│   ├── models.py              # Pydantic data models
│   ├── data_pipeline.py       # Data ingestion pipeline
│   ├── rag_engine/            # RAG pipeline implementation
│   │   ├── rag_pipeline.py    # Main RAG orchestrator
│   │   └── retrieval_system.py # Document retrieval logic
│   ├── data_sources/          # API clients for paper sources
│   │   ├── arxiv_client.py
│   │   ├── pubmed_client.py
│   │   └── semantic_scholar_client.py
│   ├── llm_integration/       # LLM integration
│   │   └── gemini_client.py   # Google Gemini client
│   ├── vector_store/          # Vector storage
│   │   └── faiss_store.py     # FAISS implementation
│   ├── utils/                 # Utility modules
│   │   ├── cache_service.py   # Redis/in-memory caching
│   │   └── data_processor.py  # Data processing utilities
│   └── background_fetcher.py  # Background paper fetching
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── SearchBar.tsx
│   │   │   ├── ResultsDisplay.tsx
│   │   │   ├── PaperCard.tsx
│   │   │   └── ClaimCard.tsx
│   │   ├── services/          # API services
│   │   │   └── api.ts
│   │   ├── types/             # TypeScript type definitions
│   │   │   └── index.ts
│   │   └── App.tsx            # Main application component
│   └── package.json
├── data/                      # Runtime data storage
│   ├── vector_store/          # FAISS indices
│   └── raw_papers_*.json      # Cached paper data
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🔧 Development

### Backend Development
```bash
# Code formatting
black backend/

# Linting
flake8 backend/

# Type checking
mypy backend/

# Run tests
pytest backend/tests/
```

### Frontend Development
```bash
# Linting
npm run lint

# Type checking
npm run type-check

# Build for production
npm run build
```

## 📊 API Documentation

Once the backend is running, visit:
- **Interactive API docs**: `http://localhost:8000/docs`
- **OpenAPI schema**: `http://localhost:8000/openapi.json`

### Key Endpoints
- `POST /query` - Main search endpoint
- `GET /health` - Health check
- `GET /cache/stats` - Cache performance metrics
- `GET /background/stats` - Background fetcher statistics

## 🎯 Development Status

### ✅ Completed Features
- **Sprint 1**: Project foundation and infrastructure
- **Sprint 2**: Data pipeline and vector store setup
- **Sprint 3**: RAG engine and LLM integration
- **Sprint 4**: Basic frontend and search interface
- **Sprint 5**: Advanced features and visualizations
- **Performance Optimization**: Caching, parallel processing, background fetching

### 🚧 Current Status
The application is fully functional with:
- Real-time paper fetching from multiple sources
- AI-powered trend analysis and claim extraction
- Modern, responsive user interface
- Performance optimizations for sub-8-second search times
- Background pre-fetching of popular BCI topics

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend development
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini** for powerful AI summarization capabilities
- **arXiv, PubMed, Semantic Scholar** for providing access to scientific literature
- **FAISS** for efficient vector similarity search
- **React and FastAPI** communities for excellent frameworks

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/bci_research_scout/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/bci_research_scout/discussions)


---

**Built with ❤️ for the BCI research community**

*Powered by sedem oasis • Built for BCI researchers*
