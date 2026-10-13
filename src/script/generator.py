"""Script generator transforming shortlisted items into spoken narration."""

import datetime
import json
import os
from typing import Any, Dict, List, Optional

from src.common.models import Script, ScriptSection, Shortlist

SECTION_BUDGETS: Dict[str, Dict[str, Any]] = {  # type: ignore
    "markets": {"name": "Markets Snapshot", "target_seconds": 70},
    "fed_bsp": {"name": "Fed & BSP Updates", "target_seconds": 70},
    "big_tech": {"name": "Big Tech Headlines", "target_seconds": 80},
    "philippines": {"name": "Philippines Focus", "target_seconds": 60},
    "india": {"name": "India Focus", "target_seconds": 60},
    "world_news": {"name": "World News Roundup", "target_seconds": 80},
}


def estimate_word_count(text: str) -> int:
    """Calculate word count for a text string."""
    return len(text.split())


def generate_script(
    shortlist: Shortlist,
    target_date: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Script:
    """Generate structured episode script from shortlist."""
    if not target_date:
        target_date = shortlist.date or datetime.date.today().isoformat()

    title = f"Morning Brief - {target_date}"
    sections: List[ScriptSection] = []
    collected_sources: List[str] = []

    # Map shortlist sections by section_name
    section_map = {s.section_name: s for s in shortlist.sections}

    for section_id, meta in SECTION_BUDGETS.items():
        name = meta["name"]
        target_sec = meta["target_seconds"]

        shortlist_sec = section_map.get(section_id)
        items_payload: List[Dict[str, str]] = []
        body_lines: List[str] = []

        if shortlist_sec and shortlist_sec.selected_items:
            for item in shortlist_sec.selected_items:
                items_payload.append(
                    {
                        "id": item.id,
                        "headline": item.headline,
                        "source": item.source,
                        "url": item.url,
                    }
                )
                if item.url and item.url not in collected_sources:
                    collected_sources.append(item.url)
                body_lines.append(f"{item.headline}. {item.summary}")
        else:
            body_lines.append(
                f"No major updates reported today for {name}. Markets and regional conditions remain steady."
            )

        section_text = (
            f"Here is your {name}. " + " ".join(body_lines)
        )

        sections.append(
            ScriptSection(
                name=name,
                duration_target_seconds=target_sec,
                text=section_text,
                items=items_payload,
            )
        )

    # Calculate overall word count estimate
    total_words = sum(estimate_word_count(s.text) for s in sections)
    target_total_seconds = sum(meta["target_seconds"] for meta in SECTION_BUDGETS.values())

    script = Script(
        date=target_date,
        title=title,
        sections=sections,
        sources=collected_sources,
        word_count_estimate=total_words,
        target_duration_seconds=target_total_seconds,
    )

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        json_path = os.path.join(output_dir, "script.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(script.to_dict(), f, indent=2)

        txt_path = os.path.join(output_dir, "script.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"# {script.title}\n")
            f.write(f"Target duration: {target_total_seconds}s | Est. words: {total_words}\n\n")
            for sec in script.sections:
                f.write(f"## {sec.name} ({sec.duration_target_seconds}s target)\n")
                f.write(f"{sec.text}\n\n")

        print(f"[script] Script written to {json_path} and {txt_path}")

    return script
