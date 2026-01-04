# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bulletin is a Python data extraction pipeline that extracts Mass times, Confession times, Adoration schedules, and parish information from Catholic church bulletin PDFs across 6 Ohio dioceses (~820 parishes). It uses AI/ML (OpenAI GPT-4, local Marker OCR) to parse unstructured PDF data and stores results in a Notion database.

## Commands

```bash
# Setup (use venv)
source venv/bin/activate
pip install -r requirements.txt  # Note: pydantic versions may need updating for Python 3.13+

# Load environment variables (required before running)
set -a && source .env

# Run main pipeline
python main.py -avmec          # All parishes, verbose, mass/confession/adoration

# Common flag combinations
python main.py -m 1234         # Mass times for specific parish ID
python main.py -a -m -c        # All enabled expired parishes: mass & confession
python main.py -d -m 5678      # Dry-run (no DB update) for parish

# Test individual modules (each has __main__ block)
python download_bulletins.py
python structured_output_extract.py
python notion_stuff.py
```

**CLI Arguments:**
- `-a, --all`: Run against all enabled parishes with expired data (>7 days)
- `-d, --dry-run`: Download & process but don't update database
- `-v, --verbose`: Verbose logging
- `-m, --mass`: Extract mass times
- `-c, --confession`: Extract confession times
- `-e, --adoration`: Extract adoration times
- `-i, --information`: Extract parish contact info
- Positional args: specific parish IDs

## Architecture

**Pipeline Flow:**
```
main.py (orchestrator)
    ↓
download_bulletins.py (fetch PDF from 3 bulletin publishers)
    ↓
structured_output_extract.py (OCR via Marker + GPT-4 extraction)
    ↓
notion_stuff.py (upload to Notion DB)
    ↓
notion_to_app.py / notion_to_json.py (export)
```

**Key Files:**
- `main.py` - Entry point, orchestrates pipeline with `run_parish()` function
- `download_bulletins.py` - Downloads PDFs from Parishes Online (PO), DiscoverMass (DM), eCatholic (EC)
- `structured_output_extract.py` - GPT-4o with Pydantic structured output for parsing
- `notion_stuff.py` - Notion API CRUD operations, `ParishRow` class
- `ocr_local.py` - Local OCR using Marker (PDF→markdown), used by default
- `ocr_client.py` - Client for remote OCR server (used when `OCR_SERVER_URL` is set)
- `ocr_server/` - FastAPI server for remote OCR processing (see below)
- `ocr.py` - Azure Document Intelligence wrapper (legacy, requires Azure credentials)
- `parishIDs.csv` - Source list of 820+ parish IDs across 6 dioceses

**Data Models (Pydantic in structured_output_extract.py):**
- `MassTime`: day, time
- `ConfessionTime`: day, time, duration
- `AdorationTime`: is24hour, day, time, duration
- `ParishInfo`: address, city, zipcode, phone, website

**External Services:**
- OpenAI API (GPT-4o-2024-08-06) - Structured extraction
- Marker (local) - PDF to markdown OCR, runs locally via `ocr_local.py`
- Notion API - Parish database storage

## Environment Variables

Required in `.env` (see `.env.template`):
- `OPENAI_API_KEY`, `BULLETIN_ASSISTANT_ID`
- `NOTION_API_KEY`, `PARISH_DB_ID`

Note: Marker OCR downloads ~2GB of models to `~/.cache/huggingface/` on first run.

## CI/CD

GitHub Actions workflow (`.github/workflows/gh-actions.yml`):
- Runs `python main.py -avmec` every Saturday at 2 PM UTC
- Manual trigger available via workflow_dispatch

## Remote OCR Server (Optional)

The OCR processing can be offloaded to a remote server for better performance on dedicated hardware.

**Setup:**
```bash
# On the OCR server machine
cd ocr_server
pip install -r requirements.txt
python server.py  # or: uvicorn server:app --host 0.0.0.0 --port 8000

# Or with Docker
docker compose up --build
```

**Configuration:**
Set `OCR_SERVER_URL` in `.env` to enable remote OCR:
```bash
OCR_SERVER_URL=http://192.168.1.100:8000
```

If `OCR_SERVER_URL` is not set, local Marker OCR is used (default behavior).

**API Endpoints:**
- `POST /jobs` - Submit PDF, returns `{job_id}`
- `GET /jobs/{job_id}` - Get job status/result
- `GET /health` - Health check with queue status
