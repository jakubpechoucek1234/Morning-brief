# Ingestion Module (`src/ingest`)

## Responsibility
Polls configured news sources (RSS feeds, APIs, web releases) based on `config/sources.yaml`, normalizes items into canonical `NewsItem` objects, filters out items older than `poll_window_hours`, and persists raw ingested records for reproducibility and auditing.

## Expected Interfaces
- `ingest_sources(config_path: str = "config/sources.yaml", output_dir: Optional[str] = None) -> List[NewsItem]`:
  - **Inputs**: Path to YAML source configuration, optional destination directory for raw payloads.
  - **Outputs**: List of normalized `NewsItem` dataclass instances.
  - **Artifacts**: Stores raw normalized items in `data/{YYYY-MM-DD}/raw_items.json`.
- `fetch_source(source: SourceConfig) -> List[NewsItem]`:
  - Dispatches fetcher implementation based on source type (`rss`, `api`, `web`).
