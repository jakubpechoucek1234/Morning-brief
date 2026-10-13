"""News ingestion implementation for Morning Brief."""

import datetime
import json
import os
import uuid
from typing import Any, Dict, List, Optional

from src.common.models import NewsItem, SourceConfig

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def load_sources_config(config_path: str = "config/sources.yaml") -> List[SourceConfig]:
    """Load sources from config/sources.yaml."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Source configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    sources_raw: List[Dict[str, Any]] = []
    if yaml is not None:
        parsed = yaml.safe_load(content)
        sources_raw = parsed.get("sources", []) if isinstance(parsed, dict) else []
    else:
        # Fallback simple parser if PyYAML is not yet installed
        import re
        current: Dict[str, Any] = {}
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("- name:"):
                if current:
                    sources_raw.append(current)
                current = {"name": line.split(":", 1)[1].strip().strip('"').strip("'")}
            elif ":" in line and current:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k in ("priority", "poll_window_hours"):
                    try:
                        current[k] = int(v)
                    except ValueError:
                        current[k] = 0
                else:
                    current[k] = v
        if current:
            sources_raw.append(current)

    configs: List[SourceConfig] = []
    for s in sources_raw:
        configs.append(
            SourceConfig(
                name=str(s.get("name", "")),
                type=str(s.get("type", "rss")),
                url=str(s.get("url", "")),
                region=str(s.get("region", "global")),
                topic=str(s.get("topic", "world_news")),
                priority=int(s.get("priority", 1)),
                poll_window_hours=int(s.get("poll_window_hours", 24)),
            )
        )
    return configs


def get_starter_items_scaffold() -> List[NewsItem]:
    """Generate representative starter items for scaffold testing."""
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return [
        NewsItem(
            id=str(uuid.uuid4())[:8],
            headline="Global equities steady as bond yields ease ahead of inflation report",
            summary="Major stock indexes held firm while benchmark treasury yields pulled back.",
            source="Reuters Markets",
            url="https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
            region="global",
            topic="markets",
            published_at=now_iso,
        ),
        NewsItem(
            id=str(uuid.uuid4())[:8],
            headline="Federal Reserve signals cautious patience on future interest rate trajectory",
            summary="Policymakers highlighted balanced labor market dynamics and inflation trends.",
            source="Federal Reserve Board",
            url="https://www.federalreserve.gov/feeds/press_all.xml",
            region="US",
            topic="central_bank",
            published_at=now_iso,
        ),
        NewsItem(
            id=str(uuid.uuid4())[:8],
            headline="Bangko Sentral ng Pilipinas maintains key policy rate to preserve price stability",
            summary="The Monetary Board kept the target reverse repurchase rate unchanged.",
            source="Bangko Sentral ng Pilipinas",
            url="https://www.bsp.gov.ph/SitePages/MediaAndResearch/MediaReleases.aspx",
            region="Philippines",
            topic="central_bank",
            published_at=now_iso,
        ),
        NewsItem(
            id=str(uuid.uuid4())[:8],
            headline="Leading tech companies announce next-generation AI model inference efficiencies",
            summary="Breakthroughs in chip architecture and quantized models reduce inference costs.",
            source="TechCrunch",
            url="https://techcrunch.com/feed/",
            region="global",
            topic="big_tech",
            published_at=now_iso,
        ),
        NewsItem(
            id=str(uuid.uuid4())[:8],
            headline="Philippine exports and service sector expand in latest quarterly economic reading",
            summary="Services exports and domestic investment supported headline growth figures.",
            source="Philippine News Agency",
            url="https://www.pna.gov.ph/rss/business",
            region="Philippines",
            topic="philippines_focus",
            published_at=now_iso,
        ),
        NewsItem(
            id=str(uuid.uuid4())[:8],
            headline="India industrial output gains momentum with manufacturing and infrastructure uptick",
            summary="Capital goods and core sector infrastructure registered robust year-on-year gains.",
            source="The Economic Times",
            url="https://economictimes.indiatimes.com/rssfeedstopstories.cms",
            region="India",
            topic="india_focus",
            published_at=now_iso,
        ),
        NewsItem(
            id=str(uuid.uuid4())[:8],
            headline="International climate and energy summit reaches consensus on grid resilience targets",
            summary="Delegates agreed on multilateral funding mechanisms to modernize transmission networks.",
            source="BBC World News",
            url="https://feeds.bbci.co.uk/news/world/rss.xml",
            region="global",
            topic="world_news",
            published_at=now_iso,
        ),
    ]


def ingest_sources(
    config_path: str = "config/sources.yaml",
    output_dir: Optional[str] = None,
    use_scaffold_items: bool = True,
) -> List[NewsItem]:
    """Ingest sources defined in configuration and return normalized items.

    In MVP scaffold mode, loads source configs and generates representative items
    ready for the ranking and shortlist pipeline.
    """
    sources = load_sources_config(config_path)
    print(f"[ingest] Loaded {len(sources)} sources from {config_path}")

    # For scaffold phase, return representative starter items
    items = get_starter_items_scaffold()

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        raw_output_path = os.path.join(output_dir, "raw_items.json")
        with open(raw_output_path, "w", encoding="utf-8") as f:
            json.dump([item.to_dict() for item in items], f, indent=2)
        print(f"[ingest] Saved {len(items)} normalized items to {raw_output_path}")

    return items
