import importlib
import inspect
from pathlib import Path


def discover_apps() -> list[dict]:
    project_root = Path(__file__).parent.parent
    apps = []

    for child in sorted(project_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith(".") or child.name.startswith("_"):
            continue
        if child.name in ("scheduler_ui", "data", "node_modules", ".venv", "__pycache__"):
            continue

        main_py = child / "main.py"
        if main_py.exists():
            has_main = _has_main_function(main_py)
            apps.append({
                "id": child.name,
                "name": child.name.replace("_", " ").title(),
                "path": str(child),
                "module": f"{child.name}.main",
                "has_main": has_main,
                "has_env": (child / ".env").exists(),
                "has_env_example": (child / ".env.example").exists(),
            })

    return apps


def _has_main_function(main_py: Path) -> bool:
    try:
        content = main_py.read_text()
        return "def main(" in content
    except Exception:
        return False
