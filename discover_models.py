#!/usr/bin/env python3
"""
Standalone CLI tool to discover available free models from opencode-to-openai gateway.
Auto-starts the gateway if not running, stops it after if we started it.

Usage:
    python discover_models.py                          # List free models
    python discover_models.py --all                    # List all models
    python discover_models.py --url http://host:port   # Custom gateway URL
    python discover_models.py --test <model_id>        # Quick test a specific model
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scheduler_ui.gateway_manager import GatewayManager
from openai import OpenAI


def list_models(base_url: str, free_only: bool = True) -> list[dict]:
    client = OpenAI(base_url=f"{base_url}/v1", api_key="not-needed")
    models = client.models.list()
    all_models = [{"id": m.id, "owned_by": getattr(m, "owned_by", "unknown")} for m in models.data]
    if free_only:
        return [m for m in all_models if "free" in m["id"].lower()]
    return all_models


def test_model(base_url: str, model_id: str) -> bool:
    client = OpenAI(base_url=f"{base_url}/v1", api_key="not-needed")
    response = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": "Say 'hello' in one word."}],
        max_tokens=10,
    )
    return bool(response.choices[0].message.content.strip())


def main():
    parser = argparse.ArgumentParser(description="Discover free models from opencode-to-openai gateway")
    parser.add_argument("--url", default="http://127.0.0.1:8083", help="Gateway URL (default: http://127.0.0.1:8083)")
    parser.add_argument("--test", metavar="MODEL_ID", help="Test a specific model with a minimal prompt")
    parser.add_argument("--all", action="store_true", help="Show all models, not just free ones")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    gw = GatewayManager.get_instance()
    try:
        gw.acquire()
    except Exception as e:
        print(f"Error: Could not start gateway: {e}")
        sys.exit(1)

    try:
        if args.test:
            print(f"Testing model: {args.test}")
            ok = test_model(args.url, args.test)
            if ok:
                print("Model responded successfully.")
            else:
                print("Model returned empty response.")
                sys.exit(1)
        else:
            free_only = not args.all
            models = list_models(args.url, free_only=free_only)
            if not models:
                print("No models found.")
                sys.exit(1)

            if args.json:
                print(json.dumps(models, indent=2))
            else:
                label = "Free models" if free_only else "All models"
                print(f"\n{label} on {args.url}:\n")
                for m in sorted(models, key=lambda x: x["id"]):
                    print(f"  {m['id']:<45} (owner: {m['owned_by']})")
                print(f"\nTotal: {len(models)} models")
                print("\nTo use a model, set LLM_MODEL in telegram_reader/.env")
                print("Example: LLM_MODEL=opencode/mimo-v2.5-free")
    except Exception as e:
        print(f"Error connecting to gateway at {args.url}: {e}")
        sys.exit(1)
    finally:
        gw.release()


if __name__ == "__main__":
    main()
