# NetScout — Intelligent Web Exploration & Visual Intelligence Platform

Two modules in one browser app:

- **WebGraph** — paste a URL and get an interactive, lazily-expandable graph of its
  hyperlink structure. Every node carries a green/amber/red spam badge scored from
  VirusTotal, Google Safe Browsing, SSL validity, domain age and URL heuristics.
  Broken links (4xx/5xx) are flagged; export the graph as PNG/SVG; filter by keyword;
  crawl depth is configurable (1–5).
- **ImageTrace** — upload an image and it's fingerprinted locally (perceptual hash),
  EXIF is extracted (GPS, camera, timestamp), then submitted to Bing Visual Search +
  Google Cloud Vision simultaneously. Results are sorted chronologically to surface
  the earliest publisher, with similarity scores, and export to PDF/CSV.

Shared: JWT auth (bcrypt), personal history dashboard, Redis-backed rate limiting
and daily quotas.

## Stack

React 18 + TypeScript + Tailwind + React Flow/D3 · FastAPI (Python 3.11) ·
Playwright (headless Chromium) · Celery + Redis · PostgreSQL 15 · Docker Compose

## Quick start

```bash
cp .env.example .env        # then edit SECRET_KEY (and API keys when you have them)
docker compose up --build
```

- App: http://localhost:8080
- API docs: http://localhost:8000/docs

Register an account, then use the WebGraph / ImageTrace tabs.

## API keys (optional but recommended)

| Env var | Service | Without it |
|---|---|---|
| `VIRUSTOTAL_API_KEY` | virustotal.com → API key | Spam score uses remaining signals |
| `GOOGLE_SAFE_BROWSING_API_KEY` | Google Cloud → Safe Browsing API | Same as above |
| `BING_VISUAL_SEARCH_API_KEY` | Azure → Bing Visual Search resource | ImageTrace returns no web matches* |
| `GOOGLE_VISION_API_KEY` | Google Cloud → Vision API (API-key auth) | Same as above |

\* Perceptual hashing, EXIF extraction and the local-cache lookup still work.
Keys are read once at container start — restart after editing `.env`.

## Local development (no Docker)

Backend:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
# point DATABASE_URL/REDIS_URL at local services, then:
uvicorn app.main:app --reload            # API on :8000
celery -A app.celery_app.celery_app worker --loglevel=info
```

Frontend:
```bash
cd frontend
npm install
npm run dev                              # dev server on :5173, proxies /api → :8000
```

## Architecture notes

- Crawls and image searches run as **Celery tasks**; the API returns job IDs the
  frontend polls, so long Playwright sessions never block requests.
- Spam scores are cached in Postgres (`url_scores`, 12 h TTL) to spare API quotas.
- Image uploads are cached by perceptual hash: a ≥92 % hash match reuses previous
  results instantly.
- Daily quotas (50 crawls / 25 image searches) and 30 req/min rate limiting live
  in Redis; tune via `.env`.
- All external integrations degrade gracefully: missing keys or network failures
  reweight the spam score across available signals instead of erroring.
