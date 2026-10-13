# Common Module (`src/common`)

## Responsibility
Provides shared domain models, configuration loaders, schema validation utilities, and logging used across all pipeline stages.

## Expected Interfaces
- `models.py`: Data structures representing core domain entities:
  - `SourceConfig`: Configuration schema for an ingestion source.
  - `NewsItem`: Canonical normalized news item produced by ingestion.
  - `ShortlistItem`: Selected news item annotated with section allocation and score.
  - `RejectedItem`: News item filtered out during deduplication/ranking with rejection reason.
  - `Shortlist`: Collection of per-section selected items and rejected candidates.
  - `ScriptSection`: Script text and timing budget for an episode section.
  - `Script`: Complete episode narration script conforming to `schemas/script.schema.json`.
- `schema_validator.py`: Helper functions to validate Python dictionaries / JSON payloads against schemas in `schemas/`.
