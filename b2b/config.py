"""Central settings, loaded from the .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

MODEL = os.getenv("MODEL", "gemini-2.5-flash")
DB_PATH = Path(os.getenv("DB_PATH", str(ROOT / "ideas.db")))
REPORTS_DIR = ROOT / "reports"
ENABLE_SEARCH = os.getenv("ENABLE_SEARCH", "true").lower() in ("1", "true", "yes")
CALL_DELAY = float(os.getenv("CALL_DELAY", "2"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "4"))
