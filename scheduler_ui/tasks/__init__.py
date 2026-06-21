import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from ..models import db, RunLog
from ..gateway_manager import GatewayManager

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent


def run_task(job_id: str, module_path: str, extra_args: list[str] = None):
    log_entry = RunLog(job_id=job_id, started_at=datetime.utcnow(), status="running")
    db.session.add(log_entry)
    db.session.commit()

    app_dir = PROJECT_ROOT / module_path.replace(".", "/").rsplit("/", 1)[0]
    cmd = [sys.executable, "main.py"]
    if extra_args:
        cmd.extend(extra_args)

    env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}

    gw = GatewayManager.get_instance()
    try:
        gw.acquire()
    except Exception as e:
        log.warning(f"Gateway unavailable: {e}. Task will run without LLM support.")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(app_dir),
            env=env,
        )
        log_entry.output = result.stdout
        log_entry.error = result.stderr
        log_entry.status = "success" if result.returncode == 0 else "failed"
    except subprocess.TimeoutExpired:
        log_entry.status = "failed"
        log_entry.error = "Task timed out after 300 seconds"
    except Exception as e:
        log_entry.status = "failed"
        log_entry.error = str(e)
    finally:
        gw.release()
        log_entry.finished_at = datetime.utcnow()
        db.session.commit()

    return log_entry
