import json
from pathlib import Path


class StateManager:
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self._ensure_dir()
        self.data = self._load()

    def _ensure_dir(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict:
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {"last_update_id": 0, "last_run": None}

    def save(self):
        with open(self.state_file, "w") as f:
            json.dump(self.data, f, indent=2, default=str)

    @property
    def last_update_id(self) -> int:
        return self.data.get("last_update_id", 0)

    @last_update_id.setter
    def last_update_id(self, value: int):
        self.data["last_update_id"] = value

    @property
    def last_run(self):
        return self.data.get("last_run")

    @last_run.setter
    def last_run(self, value):
        self.data["last_run"] = value
