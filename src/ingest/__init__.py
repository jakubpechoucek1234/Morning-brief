"""News ingestion package for Morning Brief."""

from .ingester import ingest_sources, load_sources_config

__all__ = ["ingest_sources", "load_sources_config"]
