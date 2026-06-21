import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENCODE_GATEWAY_URL = os.getenv("OPENCODE_GATEWAY_URL", "http://127.0.0.1:8083")
OPENCODE_GATEWAY_PATH = os.getenv("OPENCODE_GATEWAY_PATH", "./opencode-to-openai")
LLM_MODEL = os.getenv("LLM_MODEL", "opencode/mimo-v2.5-free")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")
STATE_FILE = BASE_DIR / "data" / "state.json"

def validate():
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not GMAIL_ADDRESS:
        missing.append("GMAIL_ADDRESS")
    if not GMAIL_APP_PASSWORD:
        missing.append("GMAIL_APP_PASSWORD")
    if not RECIPIENT_EMAIL:
        missing.append("RECIPIENT_EMAIL")
    if missing:
        raise EnvironmentError(f"Missing required env vars: {', '.join(missing)}")
