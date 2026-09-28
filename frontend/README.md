# 🤖 QA Assistant — Agentic AI for Test Failure Analysis

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22793445.svg)](https://doi.org/10.5281/zenodo.22793445)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-green)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

An agentic AI system that automatically classifies software test failures as **bugs** or **failed testcases** and takes appropriate action — generating code fixes or creating Jira tickets automatically.

---

## 📄 Research Papers

| Paper | DOI | Venue |
|-------|-----|-------|
| QA Assistant: An Agentic AI System for Intelligent Test Failure Classification | [10.5281/zenodo.22793445](https://doi.org/10.5281/zenodo.22793445) | Zenodo, Sep 2026 |
| When to Use ML, LLM, or Hybrid for Test Failure Classification | [10.5281/zenodo.22902516](https://doi.org/10.5281/zenodo.22902516) | Zenodo, Sep 2026 |

---

## 🎯 What It Does
User pastes failing test → AI classifies in <1ms (XGBoost)
↓
Is it a BUG? Is it a FAILED TESTCASE?
↓ ↓
Creates Jira ticket Generates fixed code
(human approves first) + best practices
↓ ↓
Multi-turn chat to continue debugging with full context


---

## 🏗️ Architecture

**5 AI Agents orchestrated by LangGraph:**

Input (logs + description + code)
↓
Framework Detector (Selenium/API/DB/pytest)
↓
Classifier Agent (XGBoost ML — <1ms)
↓ ↓
Bug Handler Failed TC Handler
↓ ↓
Jira Generator Code Suggestions
(human approval) (improved code)
↓ ↓
Multi-turn Chat (session memory)


---

## 📊 Results

### Classification Accuracy
| Method | Accuracy | Avg Time |
|--------|----------|----------|
| Pure LLM (Llama 3.2) | 70.0% | 11.34s |
| Pure XGBoost | 76.7% | 0.001s |
| Hybrid ML+LLM | 76.7% | 42.42s |

### Framework-wise Accuracy
| Framework | LLM | XGBoost | Hybrid |
|-----------|-----|---------|--------|
| Selenium | 60% | **90%** | 90% |
| pytest | 71% | **79%** | 79% |
| pytest-requests | **67%** | 33% | 33% |
| SQLAlchemy | **100%** | 67% | 67% |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Orchestration | LangGraph + LangChain |
| LLM (local) | Ollama + Llama 3.2 |
| LLM (cloud) | Groq API |
| ML Classifier | XGBoost (52 features) |
| Backend | FastAPI + SQLAlchemy + SQLite |
| Frontend | React + Vite + Tailwind CSS |
| Integration | Jira REST API v3 |
| Deployment | Railway (backend) + Vercel (frontend) |

---

## 🚀 Setup and Run

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama installed (for local LLM)
- Jira account (free tier works)

### Backend Setup

```bash
# 1. Clone the repository
git clone https://github.com/vaish0202/qa-assistant.git
cd qa-assistant

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env with your credentials

# 5. Pull Ollama model (for local inference)
ollama pull llama3.2

# 6. Train ML classifier
python -m ml_classifier.train

# 7. Start backend
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Access the Application

Frontend: http://localhost:5173
API Docs: http://localhost:8000/docs


---

## ⚙️ Environment Variables

Create `.env` file in root:

```env
# LLM Configuration
OLLAMA_MODEL=llama3.2
GROQ_API_KEY=your_groq_key_here  # optional, for cloud deployment

# Jira Integration
JIRA_URL=https://yourname.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=your_jira_token
JIRA_PROJECT_KEY=QA
```

---

## 📁 Project Structure

qa-assistant/
├── agents/ # AI Agents
│ ├── classifier.py # Hybrid ML+LLM classifier
│ ├── failed_testcase.py # Failed test analysis
│ ├── bug_handler.py # Bug analysis
│ ├── jira_generator.py # Jira ticket preparation
│ ├── code_suggestions.py # Code fix generation
│ ├── graph.py # LangGraph orchestration
│ ├── framework_detector.py # Testing framework detection
│ ├── prompts.py # Framework-specific prompts
│ ├── project_context.py # Project-aware context
│ └── conversation.py # Multi-turn chat memory
├── ml_classifier/ # XGBoost ML Pipeline
│ ├── feature_extractor.py # 52 feature extraction
│ ├── training_data.py # Labeled training examples
│ ├── train.py # Model training
│ └── predict.py # Fast prediction (<1ms)
├── api/ # Additional API routes
│ ├── projects.py # Project management
│ └── chat.py # Conversation endpoints
├── auth/ # Authentication
├── database/ # SQLAlchemy models
├── integrations/ # Jira API integration
├── evaluation/ # Evaluation scripts
│ ├── run_eval.py # Full evaluation
│ ├── run_xgboost_only.py # XGBoost only
│ ├── run_llm_only.py # LLM only
│ └── statistical_tests.py # Statistical analysis
├── sample_data/ # 30 labeled test cases
├── frontend/ # React frontend
│ └── src/
│ ├── pages/ # Login, Analyze, History
│ └── components/ # Sidebar, ResultCard
├── main.py # FastAPI entry point
├── requirements.txt # Python dependencies
└── Dockerfile # Docker configuration


---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze` | Main analysis endpoint |
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/register` | User register |
| GET | `/api/history` | Past analyses |
| POST | `/api/chat/followup` | Multi-turn chat |
| POST | `/api/projects/create` | Create project profile |
| POST | `/api/jira/create` | Human-approved Jira ticket |
| GET | `/api/health` | Health check |

---

## 🧪 Running Evaluations

```bash
# Full hybrid evaluation (30 test cases)
python evaluation/run_eval.py

# XGBoost only (no LLM)
python evaluation/run_xgboost_only.py

# LLM only (no ML)
python evaluation/run_llm_only.py

# Statistical significance tests
python evaluation/statistical_tests.py

# Framework-wise analysis
python evaluation/framework_analysis.py

# Adaptive classifier
python evaluation/run_adaptive.py
```

---

## 🐳 Docker Deployment

```bash
# Build image
docker build -t qa-assistant .

# Run container
docker run -p 8000:8000 --env-file .env qa-assistant
```

---

## 🌐 Cloud Deployment

**Backend:** Railway
Connect GitHub repo to Railway
Add environment variables
Deploy automatically

**Frontend:** Vercel
Import frontend folder to Vercel
Set VITE_API_URL to Railway URL
Deploy

---

## 📈 Key Features

- ✅ **Hybrid ML+LLM Classification** — XGBoost for speed, LLM for quality
- ✅ **Multi-Framework Support** — Selenium, API, Database, Unit testing
- ✅ **Project Context System** — Tech-stack aware suggestions
- ✅ **Multi-turn Conversation** — Chat with full session memory
- ✅ **Human-in-Loop Jira** — Review before ticket creation
- ✅ **Framework-Adaptive** — Best method per detected framework
- ✅ **Zero API Cost** — Runs fully local with Ollama

---

## 👩‍💻 Author

**Vaishnavi Likhe** — Independent Researcher

- GitHub: [@vaish0202](https://github.com/vaish0202)
- Papers: [Zenodo Profile](https://zenodo.org/search?q=Likhe%20Vaishnavi)

---

## 📜 License

MIT License — see [LICENSE](LICENSE) file

---

## 🙏 Acknowledgements

Built with [LangGraph](https://langchain-ai.github.io/langgraph/),
[LangChain](https://langchain.com),
[XGBoost](https://xgboost.readthedocs.io),
[Ollama](https://ollama.com),
[FastAPI](https://fastapi.tiangolo.com)