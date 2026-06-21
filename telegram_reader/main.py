import argparse
import sys
import logging
from datetime import datetime
from pathlib import Path

(Path(__file__).parent / "data").mkdir(exist_ok=True)

from config import (
    TELEGRAM_BOT_TOKEN, OPENCODE_GATEWAY_URL, LLM_MODEL,
    GMAIL_ADDRESS, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL,
    STATE_FILE, validate,
)
from state import StateManager
from telegram_bot import TelegramBot
from url_processor import process_urls
from summarizer import OpenAISummarizer
from email_sender import EmailSender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "data" / "run.log"),
    ],
)
log = logging.getLogger(__name__)


def run(dry_run: bool = False, force: bool = False, skip_llm: bool = False):
    log.info("Starting Telegram digest run")
    validate()

    state = StateManager(STATE_FILE)
    bot = TelegramBot(TELEGRAM_BOT_TOKEN)

    try:
        last_id = 0 if force else state.last_update_id
        log.info(f"Fetching messages after update_id={last_id}")
        bot.clear_conflicts()
        messages = bot.fetch_new_messages(last_id)

        if not messages:
            log.info("No new messages found")
            state.last_run = datetime.now().isoformat()
            state.save()
            return

        log.info(f"Found {len(messages)} new messages")
        if not skip_llm:
            summarizer = OpenAISummarizer(OPENCODE_GATEWAY_URL, LLM_MODEL)
        notes = []

        for msg in messages:
            log.info(f"Processing message {msg['message_id']}: {len(msg['urls'])} URLs")
            url_contents = process_urls(msg["urls"])

            for item in url_contents:
                if skip_llm:
                    content = item["content"]
                    summary_text = content[:200] + "..." if len(content) > 200 else content
                    notes.append({
                        "title": item.get("title") or "Untitled",
                        "url": item["url"],
                        "summary": summary_text,
                        "topics": [],
                        "original_text": msg["text"],
                    })
                else:
                    summary = summarizer.summarize(item["content"], item["url"])
                    notes.append({
                        "title": summary.get("title", item.get("title", "Untitled")),
                        "url": item["url"],
                        "summary": summary.get("summary", ""),
                        "topics": summary.get("topics", []),
                        "deep_dive": summary.get("deep_dive", []),
                        "original_text": msg["text"],
                    })

            state.last_update_id = max(state.last_update_id, msg["update_id"])

        if dry_run:
            log.info("Dry run — skipping email send")
            for n in notes:
                log.info(f"  [{n['title']}] {n['url']}")
        else:
            sender = EmailSender(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            run_date = datetime.now().strftime("%B %d, %Y")
            subject, html = sender.build_digest_email(notes, run_date)
            sender.send(RECIPIENT_EMAIL, subject, html)
            log.info(f"Email sent to {RECIPIENT_EMAIL} with {len(notes)} notes")

        state.last_run = datetime.now().isoformat()
        state.save()
        log.info("Run completed successfully")

    except Exception as e:
        log.error(f"Run failed: {e}", exc_info=True)
        raise
    finally:
        bot.close()


def _print_models():
    try:
        all_models = OpenAISummarizer.list_models(OPENCODE_GATEWAY_URL)
        free_models = [m for m in all_models if "free" in m["id"].lower()]
        if not free_models:
            print("No free models found. Is the gateway running?")
            return
        print(f"\nFree models on {OPENCODE_GATEWAY_URL}:\n")
        for m in sorted(free_models, key=lambda x: x["id"]):
            print(f"  {m['id']:<40} (owner: {m['owned_by']})")
        print(f"\nTotal: {len(free_models)} free models (out of {len(all_models)} total)")
        print(f"\nSet LLM_MODEL in .env to one of the above.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Telegram Digest - fetch, summarize, email")
    parser.add_argument("--dry-run", action="store_true", help="Process messages but don't send email")
    parser.add_argument("--force", action="store_true", help="Ignore saved state, process all available messages")
    parser.add_argument("--skip-llm", action="store_true", help="Skip LLM summarization")
    parser.add_argument("--list-models", action="store_true", help="List available free models from gateway and exit")
    args = parser.parse_args()

    if args.list_models:
        _print_models()
        return

    try:
        run(dry_run=args.dry_run, force=args.force, skip_llm=args.skip_llm)
    except EnvironmentError as e:
        log.error(str(e))
        sys.exit(1)
    except Exception as e:
        log.error(f"Fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
