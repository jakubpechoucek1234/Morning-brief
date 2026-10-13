# Morning Brief

Morning Brief is an automated daily ~7–8 minute private podcast news briefing delivered directly to subscribers in standard podcast players (Apple Podcasts, Overcast, Pocket Casts, Spotify). Designed for busy professionals, each episode delivers a structured, noise-free summary covering financial market movements, central bank policy updates (Federal Reserve and Bangko Sentral ng Pilipinas), major big tech developments, dedicated one-minute spotlights on the Philippines and India, and a crisp world news roundup.

---

## Architecture Stages

The automation runs sequentially through five distinct stages:

```
[ Ingest ] ──▶ [ Rank & Dedupe ] ──▶ [ Script Generation ] ──▶ [ TTS Audio ] ──▶ [ Publish & Feed ]
 (sources)      (shortlist.json)        (script.json)            (.mp3)             (podcast.xml)
```

1. **Ingest (`src/ingest`)**  
   Monitors configured feeds defined in `config/sources.yaml` across RSS, API, and web endpoints. Normalizes candidate stories into uniform `NewsItem` records within the defined lookback window (`poll_window_hours`).

2. **Rank & Shortlist (`src/rank`)**  
   Deduplicates similar stories, calculates relevance and recency scores, and assigns selected stories to episode sections. Produces `shortlist.json` conforming to `schemas/shortlist.schema.json`, explicitly tracking rejected candidates and reasons.

3. **Script Generation (`src/script`)**  
   Transforms shortlisted stories into a read-ready spoken script conforming to the episode timing budget (420–480 seconds total at ~150 words/min):
   - **Markets Snapshot**: ~70s
   - **Fed & BSP Updates**: ~70s
   - **Big Tech Headlines**: ~80s
   - **Philippines Focus**: ~60s
   - **India Focus**: ~60s
   - **World News Roundup**: ~80s  
   Emits `script.json` conforming to `schemas/script.schema.json` and human-readable `script.txt`.

4. **TTS Narration (`src/tts`)**  
   Synthesizes script sections into podcast-ready audio (`morning-brief-{date}.mp3`). Supports pluggable TTS providers (ElevenLabs, OpenAI Audio) with an offline mock mode for CI/CD runs.

5. **Publishing (`src/publish`)**  
   Updates the podcast RSS 2.0 XML feed (`podcast.xml`) with iTunes extensions and audio enclosure metadata, stages artifacts to private object storage, and emits `run_report.json`.

---

## Repository Structure

```
├── .github/workflows/
│   └── daily-brief.yml        # Scheduled daily pipeline workflow
├── config/
│   └── sources.yaml           # Curated list of starter news sources
├── schemas/
│   ├── script.schema.json     # JSON schema for narration script output
│   └── shortlist.schema.json  # JSON schema for candidate shortlist output
├── src/
│   ├── common/                # Shared domain models and validation utilities
│   ├── ingest/                # News fetchers and normalization logic
│   ├── rank/                  # Story scoring, deduplication, and selection
│   ├── script/                # Spoken script drafting and duration budgeting
│   ├── tts/                   # Audio synthesis adapters and mastering
│   ├── publish/               # Podcast RSS generator and storage publisher
│   └── main.py                # Command-line entrypoint for pipeline stages
├── data/
│   └── .gitkeep               # Local run artifacts (gitignored)
└── requirements.txt           # Python dependencies
```

---

## Local Run Expectations

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- pip

### Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running Pipeline Stages
You can run the entire pipeline end-to-end or individual stages via `src.main`:

```bash
# Run entire pipeline end-to-end (uses mock TTS in scaffold mode)
python -m src.main --stage all

# Run specific stage
python -m src.main --stage ingest
python -m src.main --stage rank
python -m src.main --stage script
python -m src.main --stage tts
python -m src.main --stage publish

# Target a specific briefing date (defaults to today)
python -m src.main --stage all --date 2026-10-13
```

Generated outputs will be saved to `data/{YYYY-MM-DD}/`:
- `raw_items.json`: Ingested raw news candidates
- `shortlist.json`: Shortlisted and rejected items
- `script.json` & `script.txt`: Formatted narration script
- `morning-brief-{date}.mp3`: Synthesized podcast audio
- `podcast.xml`: Private podcast RSS feed
- `run_report.json`: Execution summary metrics

---

## Required Secret Placeholders

When connecting external production services, configure the following secrets in repository settings or your local `.env` file:

| Secret Name | Service | Purpose |
|-------------|---------|---------|
| `OPENAI_API_KEY` | OpenAI / LLM | Automated script generation and copy editing |
| `ANTHROPIC_API_KEY` | Anthropic / LLM | Alternative model provider for script generation |
| `ELEVENLABS_API_KEY` | ElevenLabs | High-fidelity voice synthesis for TTS |
| `ELEVENLABS_VOICE_ID` | ElevenLabs | Voice identifier for briefing narrator |
| `PODCAST_STORAGE_KEY_ID` | AWS S3 / Cloudflare R2 | Storage access key ID for audio hosting |
| `PODCAST_STORAGE_SECRET` | AWS S3 / Cloudflare R2 | Storage secret key for audio hosting |
| `PODCAST_BUCKET_NAME` | AWS S3 / Cloudflare R2 | Destination bucket name for episode audio |
| `PODCAST_PRIVATE_FEED_URL`| CDN / Reverse Proxy | Tokenized or unguessable private podcast feed URL |

*(No real credentials are stored in this repository; placeholders are mocked for scaffold execution.)*

