# 🎲 Tabletop Sage

> **RAG-Powered Board Game Companion & Rules Referee**  
> Never pause game night for a 20-minute rules debate again. Search official rulebooks, curate your personal library, and get instant, citation-backed answers grounded directly in official game documentation.

---

## 🌟 Key Features

1. **🔍 Board Game Bank (Discovery)**
   - Search and browse a community bank of board game rulebooks.
   - Filter games by title, summary, or gameplay mechanics.

2. **📚 Personal Game Library**
   - Save your favorite games to your personal library for 1-click access during game sessions.
   - Track uploaded games and manage your own collection.

3. **🤖 Game-Scoped RAG Rules Referee**
   - Ask natural-language rules questions (e.g., *"How many victory points do I need to win Catan?"*, *"Can I trade properties while in Jail in Monopoly?"*).
   - **Zero-hallucination guardrail (`temperature: 0.0`)**: Vector search in ChromaDB is strictly scoped to the selected `game_id` with metadata filtering.
   - **Transparent Citations & Confidence**: Returns source section excerpts and confidence scores with every answer.

4. **📖 Official Rulebook Viewer**
   - Read full `.txt` and `.md` rulebook documents directly inside the interactive workspace.

5. **📤 Community Game Ingestion**
   - Upload new board games and their official rulebooks (`.txt`, `.md`).
   - Automatically parses, chunks with sliding character windows, and indexes embeddings into ChromaDB on the fly.

6. **🔒 Secure JWT Authentication**
   - User account registration and login with native `bcrypt` password hashing and signed JWT bearer tokens.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/) (SQLite), [Pydantic v2](https://docs.pydantic.dev/), [bcrypt](https://pypi.org/project/bcrypt/), [python-jose](https://pypi.org/project/python-jose/) |
| **RAG & AI** | [ChromaDB](https://www.trychroma.com/) (Persistent Vector Store), [Ollama](https://ollama.com/) (`llama3.2:1b` / `llama3.1:8b`) |
| **Frontend** | [Streamlit](https://streamlit.io/), [Requests](https://requests.readthedocs.io/) |
| **DevOps** | [Docker](https://www.docker.com/), Docker Compose |

---

## 📁 Project Structure

```
tabletop_sage/
├── docker-compose.yml          # Container orchestration (ollama, backend, frontend)
├── .env.example                # Environment variables template
├── README.md                   # Project documentation
├── design_docs/
│   ├── project_proposal.md     # Approved project proposal & user stories
│   └── project_design.md       # Detailed system design & ER schema
├── backend/
│   ├── Dockerfile              # Backend container definition
│   ├── main.py                 # FastAPI application & REST route handlers
│   ├── models.py               # SQLAlchemy ORM database models
│   ├── schemas.py              # Pydantic request/response validation schemas
│   ├── auth.py                 # JWT authentication & native bcrypt utilities
│   ├── database.py             # Database engine & session management
│   ├── rag_pipeline.py         # Document chunking, ChromaDB vector indexing & Ollama LLM
│   ├── requirements.txt        # Python backend dependencies
│   ├── docs/                   # Rulebook document storage folder
│   └── tests/                  # Pytest test suites (auth, CRUD, RAG)
└── frontend/
    ├── Dockerfile              # Streamlit container definition
    ├── app.py                  # Multi-view Streamlit UI application
    ├── api_client.py           # Typed backend HTTP client wrapper
    └── requirements.txt        # Frontend Python dependencies
```

---

## 🚀 Quickstart & Local Setup

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) installed locally (or running via Docker)

### 1. Clone & Configure Environment

```bash
cd project/tabletop_sage
cp .env.example .env
```

### 2. Pull Ollama Model
In a terminal, start Ollama and pull the lightweight referee model:
```bash
ollama run llama3.2:1b
```

### 3. Run the Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start FastAPI server
uvicorn main:app --reload --port 8000
```
*API Documentation (Swagger UI) is available at: `http://localhost:8000/docs`*

### 4. Run the Streamlit Frontend

In a separate terminal:
```bash
cd frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Streamlit UI
streamlit run app.py
```
*Open your browser at `http://localhost:8501` to access the application.*

---

## 🐳 Running with Docker Compose

To launch the complete isolated stack with persistent database, vector store, and model caching:

```bash
docker-compose up --build
```

- **Streamlit Web UI**: `http://localhost:8501`
- **FastAPI API**: `http://localhost:8000`
- **Ollama API**: `http://localhost:11434`

---

## 📡 REST API Reference

### Authentication
- `POST /auth/register` — Register a new player or admin account.
- `POST /auth/token` — Authenticate credentials and receive a JWT access token.
- `GET /auth/me` — *(Protected)* Retrieve current user profile.

### Game Bank & Rulebooks
- `GET /games` — Search and browse the bank of board games (`?q=query`).
- `POST /games` — *(Protected)* Upload a new board game and index its rulebook file.
- `GET /games/{game_id}` — Get single game details.
- `GET /games/{game_id}/rulebook` — Fetch raw rulebook text.

### Personal Library
- `GET /library` — *(Protected)* List authenticated user's saved games.
- `POST /library/{game_id}` — *(Protected)* Add game to user library.
- `DELETE /library/{game_id}` — *(Protected)* Remove game from user library.

### RAG Assistant & Health
- `POST /games/{game_id}/ask` — Submit a question strictly scoped to the specified game's rulebook.
- `GET /health` — Check database, ChromaDB vector store, and Ollama connectivity.

---

## 🧪 Running Tests

To run the automated backend test suite:

```bash
cd backend
pytest tests/ -v
```

