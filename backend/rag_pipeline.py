"""
Capstone Backend — RAG Pipeline
=============================================
Implements game-scoped document ingestion, ChromaDB vector retrieval,
grounded prompt construction, and Ollama LLM generation with confidence
guardrails and source citations.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any

import chromadb
import requests

logger = logging.getLogger(__name__)

# Configuration
CHROMA_PATH = Path(os.getenv("CHROMA_PATH", "./rag_db"))
CHROMA_PATH.mkdir(parents=True, exist_ok=True)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2:1b")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.30"))

COLLECTION_NAME = "board_game_rules"

# Initialize ChromaDB Persistent Client
_chroma_client = None


def get_chroma_client() -> chromadb.PersistentClient:
    """Return a singleton ChromaDB PersistentClient."""
    global _chroma_client
    if _chroma_client is None:
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return _chroma_client


def get_rules_collection():
    """Retrieve or create the ChromaDB collection for board game rules."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ─── Document Chunking & Ingestion ────────────────────────────────────────────

def chunk_document(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> list[tuple[str, str]]:
    """
    Split rulebook text into structured (section_name, chunk_text) pairs.
    Splits by markdown headings (#, ##) or logical section breaks, then
    sub-chunks large sections with sliding windows.
    """
    if not text or not text.strip():
        return []

    # Identify heading markers or paragraphs
    lines = text.splitlines()
    sections: list[tuple[str, list[str]]] = []
    current_section = "General Rules"
    current_lines: list[str] = []

    heading_regex = re.compile(r"^(?:#{1,4}\s+|\b[A-Z0-9\s]{3,30}:?$|How to|Setup|Rules|Turn|Score|End of|Building|Trading)")

    for line in lines:
        stripped = line.strip()
        # Check if line looks like a heading
        if heading_regex.match(stripped) and len(stripped) < 60 and not stripped.endswith("."):
            if current_lines:
                sections.append((current_section, current_lines))
                current_lines = []
            current_section = stripped.lstrip("#").strip().rstrip(":")
        else:
            if stripped:
                current_lines.append(stripped)

    if current_lines:
        sections.append((current_section, current_lines))

    # Sub-chunk sections into character windows
    chunks: list[tuple[str, str]] = []
    for sec_title, sec_lines in sections:
        combined_text = "\n".join(sec_lines)
        if len(combined_text) <= chunk_size:
            if len(combined_text.strip()) > 20:
                chunks.append((sec_title, combined_text.strip()))
        else:
            # Sliding window chunking
            start = 0
            while start < len(combined_text):
                end = start + chunk_size
                chunk_str = combined_text[start:end].strip()
                if len(chunk_str) > 20:
                    chunks.append((sec_title, chunk_str))
                start += chunk_size - chunk_overlap

    # Fallback if no chunks extracted
    if not chunks and text.strip():
        chunks.append(("Overview", text.strip()[:chunk_size]))

    return chunks


def ingest_rulebook(
    file_path: Path | str,
    game_id: int,
    game_name: str,
) -> int:
    """
    Read, chunk, and index a rulebook document into ChromaDB scoped by game_id.
    Returns the number of indexed chunks.
    """
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"File not found for ingestion: {path}")
        return 0

    text = path.read_text(encoding="utf-8", errors="replace")
    chunks = chunk_document(text)
    if not chunks:
        return 0

    collection = get_rules_collection()

    # Remove any existing chunks for this game to avoid duplicate accumulation
    try:
        collection.delete(where={"game_id": game_id})
    except Exception:
        pass  # Collection might be empty or game_id doesn't exist yet

    documents = []
    metadatas = []
    ids = []

    for i, (section, chunk_text) in enumerate(chunks):
        chunk_id = f"game_{game_id}_chunk_{i}"
        documents.append(chunk_text)
        metadatas.append({
            "game_id": game_id,
            "game_name": game_name,
            "chunk_index": i,
            "section": section,
        })
        ids.append(chunk_id)

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )
    logger.info(f"Ingested {len(ids)} chunks for '{game_name}' (game_id={game_id}).")
    return len(ids)


def delete_game_from_index(game_id: int) -> bool:
    """Remove all indexed chunks for a game from ChromaDB."""
    try:
        collection = get_rules_collection()
        collection.delete(where={"game_id": game_id})
        return True
    except Exception as exc:
        logger.error(f"Failed to delete game_id={game_id} from vector store: {exc}")
        return False


# ─── Scoped Vector Retrieval ──────────────────────────────────────────────────

def retrieve_context(
    question: str,
    game_id: int,
    n_results: int = 3,
) -> list[dict[str, Any]]:
    """
    Perform a vector similarity search strictly scoped to the specified game_id.
    Returns a list of citation dictionaries with text, section, and similarity score.
    """
    collection = get_rules_collection()

    try:
        results = collection.query(
            query_texts=[question],
            where={"game_id": game_id},
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        logger.error(f"ChromaDB query failed for game_id={game_id}: {exc}")
        return []

    citations: list[dict[str, Any]] = []
    if not results or not results["documents"] or not results["documents"][0]:
        return citations

    docs = results["documents"][0]
    metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
    ids = results["ids"][0] if results.get("ids") else [""] * len(docs)
    distances = results["distances"][0] if results.get("distances") else [1.0] * len(docs)

    for doc, meta, cid, dist in zip(docs, metas, ids, distances):
        # Convert cosine distance (0=exact, 2=opposite) to 0.0 - 1.0 confidence/similarity score
        similarity = max(0.0, min(1.0, 1.0 - (dist / 2.0)))
        citations.append({
            "chunk_id": cid,
            "text": doc,
            "section": meta.get("section", "General Rules") if meta else "General Rules",
            "score": round(similarity, 3),
        })

    return citations


# ─── Grounded Answer Generation (LLM) ────────────────────────────────────────

def build_system_prompt(game_name: str, citations: list[dict[str, Any]]) -> str:
    """Construct a clear, grounded system prompt containing rulebook citations."""
    context_blocks = []
    for i, c in enumerate(citations, 1):
        context_blocks.append(
            f"--- Excerpt {i} (Section: {c['section']}) ---\n{c['text']}"
        )
    joined_context = "\n\n".join(context_blocks)

    return (
        f"You are Tabletop Sage, an expert board game rules referee for {game_name.title()}.\n"
        f"Use the official rulebook excerpts provided below to answer the user's question directly, factually, and concisely.\n\n"
        f"{joined_context}\n\n"
        f"Instructions:\n"
        f"1. Answer based strictly on the excerpts provided above.\n"
        f"2. Cite the relevant section if mentioned.\n"
        f"3. If the answer is completely missing from the excerpts, state that the rule is not covered in the provided document."
    )


def generate_answer(
    question: str,
    game_name: str,
    citations: list[dict[str, Any]],
) -> str:
    """
    Call Ollama LLM to generate a grounded answer from retrieved context.
    Falls back gracefully if the LLM service is offline.
    """
    if not citations:
        return f"I cannot find any relevant rulebook excerpts for '{game_name}' to answer your question."

    system_prompt = build_system_prompt(game_name, citations)

    # Call Ollama /api/chat
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "stream": False,
        "options": {
            "temperature": 0.0,  # Zero temperature for deterministic, factual rules answers
            "top_p": 0.9,
        },
    }

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=45,
        )
        if response.status_code == 200:
            data = response.json()
            answer_text = data.get("message", {}).get("content", "").strip()
            if answer_text:
                return answer_text
            return "No response received from the language model."
        else:
            logger.warning(f"Ollama returned status {response.status_code}: {response.text}")
            return (
                f"(LLM Service Notice: Ollama returned status {response.status_code}. "
                f"Please refer to the source citations below for the official rules excerpt.)"
            )
    except requests.exceptions.RequestException as exc:
        logger.error(f"Failed to connect to Ollama at {OLLAMA_URL}: {exc}")
        # Graceful fallback providing the retrieved rulebook excerpts
        top_excerpt = citations[0]["text"] if citations else "None"
        top_section = citations[0]["section"] if citations else "General"
        return (
            f"Ollama LLM is currently unreachable at `{OLLAMA_URL}`.\n\n"
            f"**Relevant Rulebook Excerpt ({top_section}):**\n"
            f"> {top_excerpt}\n\n"
            f"*(Start Ollama with `ollama run {MODEL_NAME}` or `docker-compose up` to enable interactive AI summaries.)*"
        )


# ─── End-to-End Query Pipeline ────────────────────────────────────────────────

def query_rag_pipeline(
    question: str,
    game_id: int,
    game_name: str,
    n_results: int = 3,
) -> dict[str, Any]:
    """
    Full RAG execution:
    1. Scoped vector retrieval in ChromaDB (where game_id == game_id)
    2. Confidence score calculation and guardrail check
    3. Grounded LLM generation with Ollama
    """
    citations = retrieve_context(question=question, game_id=game_id, n_results=n_results)

    if not citations:
        return {
            "answer": (
                f"No rulebook documentation found for '{game_name}' (ID: {game_id}) in the vector database. "
                f"Please ensure a rulebook document has been uploaded and indexed."
            ),
            "citations": [],
            "confidence": 0.0,
        }

    # Calculate overall confidence score (highest chunk similarity)
    top_score = citations[0]["score"] if citations else 0.0
    avg_score = sum(c["score"] for c in citations) / len(citations) if citations else 0.0
    confidence = round((top_score * 0.7) + (avg_score * 0.3), 3)

    # Generate answer
    answer = generate_answer(question=question, game_name=game_name, citations=citations)

    return {
        "answer": answer,
        "citations": citations,
        "confidence": confidence,
    }


# ─── Health & Diagnostics ─────────────────────────────────────────────────────

def check_rag_health() -> dict[str, str]:
    """Check connectivity to ChromaDB vector store and Ollama model server."""
    # Check ChromaDB
    try:
        col = get_rules_collection()
        count = col.count()
        chroma_status = f"healthy ({count} indexed chunks)"
    except Exception as exc:
        chroma_status = f"unhealthy: {exc!s}"

    # Check Ollama
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if resp.status_code == 200:
            models = [m.get("name") for m in resp.json().get("models", [])]
            has_model = any(MODEL_NAME in m for m in models)
            model_info = f"model '{MODEL_NAME}' available" if has_model else f"model '{MODEL_NAME}' not pulled"
            ollama_status = f"healthy ({model_info})"
        else:
            ollama_status = f"unhealthy (status {resp.status_code})"
    except Exception as exc:
        ollama_status = f"unreachable ({exc!s})"

    return {
        "vector_store": chroma_status,
        "llm": ollama_status,
    }

