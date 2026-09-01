# Capstone Project Proposal: Tabletop Sage

---

## 1. Project Name & Description
* **Project Name**: Tabletop Sage (Alternative Options: *MeepleMind*, *RuleBook AI*, *BoardGame Oracle*)
* **One-Sentence Description**: A containerized, RAG-powered board game companion and community bank where players can search available games, curate their personal library, view official rulebooks, and get instant, citation-backed answers to rules questions grounded in game-specific documentation.

---

## 2. User Stories
1. **Game Discovery & Personal Library**:
   * *As an app user*, I want to **search through a bank of available board games and add my favorites to my library**, so that I can **easily organize, track, and quickly access the games I own and play**.
2. **Game-Specific Rulebook & RAG Assistant**:
   * *As an app user*, I want to **pick any board game from my library to have access to its rulebook and a dedicated RAG assistant**, so that I can **read the rules and get instant, citation-backed answers to my questions grounded specifically in that game's documentation**.
3. **Community Game & Rulebook Uploads**:
   * *As an app user*, I want to **upload a new board game and its rulebook to the bank**, so that **other users are able to find them, add them to their libraries, and query their rules**.

---

## 3. Required Components Mapping

* **FastAPI Backend (Key Endpoints)**:
  * `POST /auth/register` & `POST /auth/token`: User registration and JWT authentication.
  * `GET /games`: Search and browse the bank of available board games with query filtering.
  * `POST /games`: Upload a new board game and its rulebook to the shared bank (triggers document chunking and vector indexing).
  * `GET /games/{game_id}/rulebook`: Retrieve the full rulebook content for reading.
  * `GET /library`, `POST /library/{game_id}`, & `DELETE /library/{game_id}`: Manage the authenticated user's personal favorites/library.
  * `POST /games/{game_id}/ask`: RAG query endpoint that answers rules questions strictly scoped to the specified game's documentation, returning answers, source citations, and confidence scores.
* **SQLAlchemy Database (Relational Schema)**:
  * **`User` Table**: `id` (PK), `username`, `hashed_password`, `role` (Admin/Player), `created_at`.
  * **`BoardGame` Table**: `id` (PK), `name`, `description`, `filename`, `uploaded_by_user_id` (FK referencing `User.id`), `uploaded_at`.
  * **`UserLibrary` (Association Table)**: `id` (PK), `user_id` (FK referencing `User.id`), `game_id` (FK referencing `BoardGame.id`), `added_at`.
  * *Relationships*: 
    * **Many-to-Many**: `User` $\leftrightarrow$ `BoardGame` through `UserLibrary` for personal collections.
    * **One-to-Many**: `User` $\rightarrow$ `BoardGame` tracking which user contributed/uploaded the game.
* **Pydantic Validation**:
  * Request/response schemas for all routes (`UserCreate`, `UserResponse`, `Token`, `GameCreate`, `GameResponse`, `LibraryItem`, `QueryRequest`, `QueryResponse`, `Citation`).
* **JWT Authentication**:
  * Secures user-specific operations (managing personal library, uploading new games, and personal session state).
* **RAG Pipeline**:
  * **ChromaDB Vector Store**: Stores embeddings of chunked rulebooks with metadata tags (`game_id`, `game_name`, `chunk_id`, `section`).
  * **Metadata-Filtered Retrieval**: Scopes similarity search strictly to the selected game (`where={"game_id": game_id}`), preventing cross-game rules contamination.
  * **Ollama LLM**: Runs `llama3.2:1b` (fast/CPU-friendly default) or `llama3.1:8b` locally to generate grounded, concise answers with direct citations.
* **Streamlit Frontend (Multi-View UI)**:
  * **Game Bank / Discovery**: Search bar with live filters and "Add to My Library" quick actions.
  * **My Library**: Interactive grid of saved games with quick access to rulebooks and chat.
  * **Game Workspace (Rulebook & Assistant)**: Split view or tabbed interface featuring the full rulebook viewer alongside the conversational RAG chatbot (with citation popups and STT voice input).
  * **Upload Portal**: Clean form to submit game metadata and upload rulebook files (`.txt`, `.md`, `.pdf`).
* **Docker Compose**:
  * Orchestrates `backend`, `frontend`, and `ollama` services into a reproducible network with persistent named volumes for SQLite database, ChromaDB vectors, and Ollama model weights.
* **Testing**:
  * Comprehensive suite of unit and integration tests using `pytest` and `fastapi.testclient` testing auth, game bank search, library CRUD, RAG retrieval filtering, and upload validation.

---

## 4. Data Source
* Initial seed data consisting of plain text (`.txt`) and Markdown (`.md`) rulebook files for popular board games (e.g., *Catan*, *Ticket to Ride*, *Carcassonne*, *Pandemic*, *Wingspan*), supplemented by community-contributed rulebooks uploaded dynamically by users.

---

## 5. Tech Stack & Speech-to-Text (STT) Feature
* **Core Stack**: FastAPI + SQLAlchemy (SQLite) + ChromaDB + Ollama + Streamlit + Docker Compose.
* **Speech-to-Text (STT) Integration**:
  * **Frontend**: `streamlit-mic-recorder` component for in-browser audio capture directly in the game chat interface.
  * **Backend**: **OpenAI Whisper** (`whisper-tiny` or `whisper-base` running locally or via API) to transcribe voice queries into text prior to RAG execution, enabling hands-free game night queries.

---

## 6. Project Risks & Backup Plans

### Risk 1: Corrupted or Malicious Rulebook Uploads in Community Bank
* **The Issue**: Community uploads might include malformed text, non-rulebook files, or unparseable formats that could break chunking or pollute search results.
* **Mitigation / Backup Plan**:
  1. Implement strict file validation (MIME-type checks, file size limits, and sanitization).
  2. Implement an automated indexing verification step during ingestion; if chunking fails or yields empty text, rollback the database entry and notify the user.
  3. Include a `status` field (`active` / `flagged`) and moderation controls so problematic rulebooks can be deactivated.

### Risk 2: Cross-Game Rules Contamination & LLM Hallucinations
* **The Issue**: Querying general vector stores might retrieve rules from the wrong game (e.g., applying Catan trading rules to Ticket to Ride), or LLMs may fabricate rules during disputed edge cases.
* **Mitigation / Backup Plan**:
  1. **Strict Metadata Scoping**: Hard-filter vector searches by `game_id` in ChromaDB so embeddings from other games are physically excluded from the retrieved context.
  2. **Grounded System Prompting**: Set temperature to `0.0` with explicit constraints: *"Answer ONLY based on the provided rulebook excerpt. If the answer is not explicitly stated in the context, clearly state that the rule is not mentioned in the provided document."*
  3. **Verifiable Citations**: Return exact section names and paragraph excerpts alongside answers in UI expanders so players can instantly verify against the official text.
