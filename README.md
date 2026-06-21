# TelegramScheduler

A Python task scheduling system that reads Telegram bot messages, summarizes linked web content via free LLM models, and emails a daily digest. Includes a Flask web UI for monitoring and managing scheduled tasks.

## Features

- Fetches new messages from a Telegram bot
- Extracts and summarizes linked web content
- Uses free LLM models via a local [opencode-to-openai](https://github.com/dxxzst/opencode-to-openai) gateway
- Emails an HTML digest with titles, summaries, topics, and deep-dive suggestions
- Flask web UI for monitoring, scheduling, and manual task execution
- Auto-discovers CLI apps — easy to extend
- Gateway auto-starts before tasks and stops after (saves resources)

## Prerequisites

- **Python 3.12+**
- **Node.js v18+** — https://nodejs.org/
- **opencode CLI** — `npm install -g opencode-ai`
- **Gmail account** with App Password enabled
- **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)

## Quick Start

### Windows

Double-click `setup.bat` — it installs everything and launches the UI.

### Manual (Any OS)

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS/Linux
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Clone and install dependencies
git clone https://github.com/<your-username>/TelegramScheduler.git
cd TelegramScheduler
uv sync

# Install the LLM gateway
git clone https://github.com/dxxzst/opencode-to-openai.git opencode-to-openai
cd opencode-to-openai && npm install && cd ..

# Configure
cd telegram_reader
cp .env.example .env
# Edit .env with your credentials (see Configuration below)
cd ..

# Run
uv run python -m scheduler_ui
# Open http://localhost:5000
```

## Configuration

Edit `telegram_reader/.env` with your credentials:

| Variable | Description | Example |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token | `123456789:ABCdef...` |
| `OPENCODE_GATEWAY_URL` | Gateway URL | `http://127.0.0.1:8083` |
| `OPENCODE_GATEWAY_PATH` | Gateway install path (relative) | `./opencode-to-openai` |
| `LLM_MODEL` | Free model to use | `opencode/mimo-v2.5-free` |
| `GMAIL_ADDRESS` | Gmail sender address | `you@gmail.com` |
| `GMAIL_APP_PASSWORD` | Gmail App Password | `xxxx-xxxx-xxxx-xxxx` |
| `RECIPIENT_EMAIL` | Digest recipient | `you@gmail.com` |

### Discovering Free Models

```bash
uv run python discover_models.py
```

Auto-starts the gateway, lists available free models, then stops the gateway.

## Usage

### Web UI

```bash
uv run python -m scheduler_ui
# Open http://localhost:5000
```

- **Dashboard** — overview of jobs and recent activity
- **Jobs** — edit cron schedules, enable/disable, run manually
- **Logs** — browse execution history with output and errors


## Cron Schedule Format

```
minute hour day month day_of_week
```

| Position | Values | Description |
|---|---|---|
| `minute` | 0-59 | Minute of the hour |
| `hour` | 0-23 | Hour of the day (24h format) |
| `day` | 1-31 | Day of the month |
| `month` | 1-12 | Month of the year |
| `day_of_week` | 0-6 (or sun-sat) | Day of the week (0=Sunday) |

### Special Characters

| Symbol | Meaning | Example |
|---|---|---|
| `*` | Any/every value | `* * * * *` = every minute |
| `*/n` | Every n units | `*/15 * * * *` = every 15 min |
| `n,m` | Specific values | `0 8,12,18 * * *` = at 8am, noon, 6pm |
| `n-m` | Range | `0 9-17 * * *` = every hour from 9am-5pm |

### Common Examples

```
* * * * *        Every minute
*/5 * * * *      Every 5 minutes
0 * * * *        Every hour (at :00)
0 0 * * *        Daily at midnight
0 9 * * *        Daily at 9:00 AM
0 9 * * 1-5      Weekdays at 9:00 AM
0 9 * * 1        Every Monday at 9:00 AM
30 8 * * 1-5     Weekdays at 8:30 AM
0 8,12,18 * * *  At 8am, 12pm, and 6pm
0 0 1 * *        First day of each month
*/30 * * * *     Every 30 minutes
0 */2 * * *      Every 2 hours
```



### CLI

```bash
# Full run with AI summaries
uv run python telegram_reader/main.py

# Dry run (no email sent)
uv run python telegram_reader/main.py --dry-run

# Skip LLM summarization
uv run python telegram_reader/main.py --skip-llm

# List available free models
uv run python telegram_reader/main.py --list-models
```

### Remote Access

The UI listens on `0.0.0.0:5000`. From another PC on your network:

```
http://<your-local-ip>:5000
```

If blocked, allow port 5000 through Windows Firewall (run as Administrator):

```powershell
netsh advfirewall firewall add rule name="Flask 5000" dir=in action=allow protocol=TCP localport=5000
```

## Adding New CLI Apps

1. Create a directory at the project root (e.g., `my_app/`)
2. Add a `main.py` with a `main()` function
3. Restart the scheduler UI — the app is auto-discovered

## How It Works

1. The scheduler triggers tasks via cron expressions
2. Before each task, `GatewayManager` starts the `opencode-to-openai` gateway if not running
3. The task runs as a subprocess with the gateway available for LLM calls
4. After the task completes, the gateway is stopped (if we started it)

This means the gateway is only running when needed — no always-on process required.

## Project Structure

```
TelegramScheduler/
├── pyproject.toml
├── setup.bat
├── start_ui.bat
├── discover_models.py
├── telegram_reader/          # CLI app: Telegram digest
│   ├── main.py
│   ├── config.py
│   ├── summarizer.py
│   ├── telegram_bot.py
│   ├── url_processor.py
│   ├── email_sender.py
│   └── templates/
└── scheduler_ui/             # Flask monitoring UI
    ├── app.py
    ├── gateway_manager.py
    ├── scheduler.py
    ├── discovery.py
    ├── tasks/
    ├── templates/
    └── static/
```

## License

[MIT](LICENSE)
