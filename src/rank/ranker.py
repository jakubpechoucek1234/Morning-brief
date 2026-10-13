"""Ranking and candidate shortlisting logic for Morning Brief."""

import datetime
import json
import os
from typing import Dict, List, Optional

from src.common.models import (
    NewsItem,
    RejectedItem,
    SectionShortlist,
    Shortlist,
    ShortlistItem,
)

TOPIC_TO_SECTION: Dict[str, str] = {
    "markets": "markets",
    "central_bank": "fed_bsp",
    "big_tech": "big_tech",
    "philippines_focus": "philippines",
    "india_focus": "india",
    "world_news": "world_news",
}

SECTION_ORDER = [
    "markets",
    "fed_bsp",
    "big_tech",
    "philippines",
    "india",
    "world_news",
]


def rank_and_shortlist(
    items: List[NewsItem],
    target_date: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Shortlist:
    """Rank ingested items and assign to sections, capturing rejected candidates."""
    if not target_date:
        target_date = datetime.date.today().isoformat()

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Buckets for each section
    section_buckets: Dict[str, List[ShortlistItem]] = {s: [] for s in SECTION_ORDER}
    rejected_items: List[RejectedItem] = []
    seen_headlines: set = set()

    # Scoring and deduplication
    for item in items:
        # Deduplication check
        norm_title = item.headline.strip().lower()
        if norm_title in seen_headlines:
            rejected_items.append(
                RejectedItem(
                    id=item.id,
                    headline=item.headline,
                    source=item.source,
                    url=item.url,
                    reason="duplicate_headline",
                    stage="deduplication",
                )
            )
            continue
        seen_headlines.add(norm_title)

        # Topic to section routing
        section_key = TOPIC_TO_SECTION.get(item.topic, "world_news")

        # Assign base score (mock priority + recency)
        score = 8.5

        shortlist_item = ShortlistItem(
            id=item.id,
            headline=item.headline,
            summary=item.summary,
            source=item.source,
            url=item.url,
            score=score,
            published_at=item.published_at,
        )

        section_buckets[section_key].append(shortlist_item)

    sections: List[SectionShortlist] = []
    for section_name in SECTION_ORDER:
        selected = section_buckets[section_name]
        sections.append(
            SectionShortlist(
                section_name=section_name,
                selected_items=selected,
                target_item_count=max(len(selected), 1),
            )
        )

    shortlist = Shortlist(
        generated_at=now_iso,
        date=target_date,
        sections=sections,
        rejected_items=rejected_items,
    )

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, "shortlist.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(shortlist.to_dict(), f, indent=2)
        print(f"[rank] Shortlist written to {out_path}")

    return shortlist
