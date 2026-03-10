# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Telegram bot built as a **Cloudflare Worker in Python** (via Pyodide). Receives Telegram webhook POSTs, generates responses using Cloudflare Workers AI (Llama 3), and stores conversation history in Cloudflare D1 (SQLite).

## Architecture

- **`src/entry.py`** — Main worker entrypoint. Exports `on_fetch(request, env)` which handles incoming Telegram webhook requests.
- **`src/submodule.py`** — Utility module (currently minimal).
- **`schema.sql`** — D1 database schema defining the `messages` table (id, chat_id, role, content, created_at).
- **`wrangler.jsonc`** — Cloudflare Workers config. Bindings: `AI` (Workers AI), `DB` (D1 database). Secret: `TELEGRAM_BOT_TOKEN`.
- **`docs/implementation_plan.md`** — Detailed architecture plan (in Portuguese).

### Request Flow

1. Telegram sends webhook POST to the Worker
2. Worker parses the update, extracts `chat_id` and `text`
3. User message is logged to D1
4. Text is sent to Cloudflare AI (`@cf/meta/llama-3-8b-instruct`)
5. AI response is sent back to Telegram via `sendMessage` API (using `js.fetch`)
6. Assistant message is logged to D1

## Commands

| Task | Command |
|------|---------|
| Local dev server | `npm run dev` (or `uv run pywrangler dev`) |
| Deploy | `npm run deploy` (or `uv run pywrangler deploy`) |
| Run all tests | `uv run pytest` |
| Run single test | `uv run pytest tests/test_entry.py::test_name` |
| Apply D1 schema (local) | `npx wrangler d1 execute bot-database --local --file=./schema.sql` |
| Apply D1 schema (remote) | `npx wrangler d1 execute bot-database --remote --file=./schema.sql` |
| Generate types | `npx wrangler types` |
| Live logs | `npx wrangler tail` |

## Python Environment

- Requires Python >=3.12 and `uv` for dependency management
- Setup: `uv venv && uv sync`
- Dependencies: `webtypy` (type hints for Web APIs), `workers-py` (dev tooling)
- Tests use `pytest` with `pytest-asyncio` and `unittest.mock`

## Cloudflare Workers Python Notes

- Python runs via Pyodide in the Workers runtime — not all Python packages are available
- Use `js.fetch`, `js.Response`, `js.Object`, `js.JSON` for Web API interop (imported from `js` module)
- Always check Cloudflare docs for current API limits and available features before making changes
- Run `npx wrangler types` after changing bindings in `wrangler.jsonc`
