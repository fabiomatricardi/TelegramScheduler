import re
import time
import httpx

BASE_URL = "https://api.telegram.org/bot{token}"

URL_PATTERN = re.compile(
    r'https?://[^\s<>"\')\]]+',
    re.IGNORECASE,
)


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.base_url = BASE_URL.format(token=token)
        self.client = httpx.Client(timeout=30)

    def clear_conflicts(self):
        self.client.get(f"{self.base_url}/deleteWebhook")

    def get_updates(self, offset: int = 0, limit: int = 100, retries: int = 3) -> list[dict]:
        params = {"offset": offset, "limit": limit, "timeout": 5}
        for attempt in range(retries):
            resp = self.client.get(f"{self.base_url}/getUpdates", params=params)
            if resp.status_code == 409 and attempt < retries - 1:
                time.sleep(3)
                continue
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                raise RuntimeError(f"Telegram API error: {data}")
            return data.get("result", [])

    def extract_messages(self, updates: list[dict]) -> list[dict]:
        messages = []
        for update in updates:
            msg = update.get("message")
            if not msg:
                continue
            text = msg.get("text", "")
            if not text:
                continue
            urls = URL_PATTERN.findall(text)
            messages.append({
                "update_id": update["update_id"],
                "message_id": msg.get("message_id"),
                "date": msg.get("date"),
                "text": text,
                "urls": urls,
                "chat_id": msg["chat"]["id"],
            })
        return messages

    def fetch_new_messages(self, last_update_id: int) -> list[dict]:
        updates = self.get_updates(offset=last_update_id + 1)
        return self.extract_messages(updates)

    def close(self):
        self.client.close()
