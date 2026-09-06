import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure backend root directory is on Python path during test execution
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Create isolated temporary paths for tests
TEMP_TEST_DIR = Path(tempfile.mkdtemp(prefix="tabletop_test_"))
TEST_DOCS_PATH = TEMP_TEST_DIR / "docs"
TEST_CHROMA_PATH = TEMP_TEST_DIR / "chroma"
TEST_DB_PATH = TEMP_TEST_DIR / "test_app.db"

os.environ["DOCS_STORAGE_PATH"] = str(TEST_DOCS_PATH)
os.environ["CHROMA_PATH"] = str(TEST_CHROMA_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"


import models  # noqa: F401, E402
from database import Base, engine  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_test_env():
    """Ensure clean test environment, tables created, and cleanup after tests."""
    TEST_DOCS_PATH.mkdir(parents=True, exist_ok=True)
    TEST_CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup temporary test directory
    shutil.rmtree(TEMP_TEST_DIR, ignore_errors=True)


