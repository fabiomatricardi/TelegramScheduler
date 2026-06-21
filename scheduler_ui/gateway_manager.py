import logging
import os
import subprocess
import threading
import time
from pathlib import Path

import httpx

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / "telegram_reader" / ".env"


def _load_env(key: str, default: str = "") -> str:
    value = os.getenv(key)
    if value:
        return value
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith(f"{key}=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return default


GATEWAY_URL = _load_env("OPENCODE_GATEWAY_URL", "http://127.0.0.1:8083")
GATEWAY_PATH = _load_env("OPENCODE_GATEWAY_PATH", "./opencode-to-openai")


class GatewayManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._ref_count = 0
        self._process: subprocess.Popen | None = None
        self._started_by_us = False
        self._inner_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "GatewayManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def is_running(self) -> bool:
        try:
            resp = httpx.get(f"{GATEWAY_URL}/v1/models", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def acquire(self):
        with self._inner_lock:
            self._ref_count += 1
            if self._ref_count == 1 and not self.is_running():
                self._start()

    def release(self):
        with self._inner_lock:
            self._ref_count -= 1
            if self._ref_count <= 0:
                self._ref_count = 0
                if self._started_by_us:
                    self._stop()

    def _start(self):
        gateway_dir = (PROJECT_ROOT / GATEWAY_PATH).resolve()
        index_js = gateway_dir / "index.js"
        node_modules = gateway_dir / "node_modules"

        if not index_js.exists():
            raise FileNotFoundError(
                f"Gateway not found at {gateway_dir}. "
                f"Run setup.bat or: git clone https://github.com/dxxzst/opencode-to-openai.git {GATEWAY_PATH}"
            )

        if not node_modules.exists():
            raise FileNotFoundError(
                f"Gateway dependencies not installed at {gateway_dir}. "
                f"Run: cd {GATEWAY_PATH} && npm install"
            )

        log.info(f"Starting opencode-to-openai gateway from {gateway_dir}")
        self._process = subprocess.Popen(
            ["node", "index.js"],
            cwd=str(gateway_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        self._started_by_us = True

        for i in range(30):
            if self.is_running():
                log.info("Gateway is ready")
                return
            time.sleep(1)

        self._stop()
        raise RuntimeError("Gateway failed to start within 30 seconds")

    def _stop(self):
        if self._process and self._process.poll() is None:
            log.info("Stopping opencode-to-openai gateway")
            try:
                self._process.terminate()
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                log.warning("Gateway did not stop gracefully, killing")
                self._process.kill()
                self._process.wait(timeout=5)
            log.info("Gateway stopped")
        self._process = None
        self._started_by_us = False
