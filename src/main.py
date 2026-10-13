"""Main CLI entrypoint for Morning Brief pipeline stages."""

import argparse
import datetime
import json
import os
import sys

from src.common.models import NewsItem, Script, ScriptSection, Shortlist
from src.ingest import ingest_sources
from src.publish import publish_episode
from src.rank import rank_and_shortlist
from src.script import generate_script
from src.tts import synthesize_briefing


def run_pipeline(stage: str = "all", target_date: str = "", config_path: str = "config/sources.yaml") -> None:
    """Run specified stage or all stages sequentially."""
    if not target_date:
        target_date = datetime.date.today().isoformat()

    output_dir = os.path.join("data", target_date)
    os.makedirs(output_dir, exist_ok=True)
    print(f"=== Morning Brief Automation | Stage: {stage} | Date: {target_date} ===")

    # STAGE 1: INGEST
    if stage in ("all", "ingest"):
        items = ingest_sources(config_path=config_path, output_dir=output_dir)
        print(f"[pipeline] Ingested {len(items)} items.")
        if stage == "ingest":
            return

    # STAGE 2: RANK
    if stage in ("all", "rank"):
        raw_items_path = os.path.join(output_dir, "raw_items.json")
        if os.path.exists(raw_items_path):
            with open(raw_items_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            items = [NewsItem(**item) for item in raw_data]
        else:
            items = ingest_sources(config_path=config_path, output_dir=output_dir)

        shortlist = rank_and_shortlist(items, target_date=target_date, output_dir=output_dir)
        print(f"[pipeline] Shortlist generated with {len(shortlist.sections)} sections.")
        if stage == "rank":
            return

    # STAGE 3: SCRIPT
    if stage in ("all", "script"):
        shortlist_path = os.path.join(output_dir, "shortlist.json")
        if not os.path.exists(shortlist_path):
            items = ingest_sources(config_path=config_path, output_dir=output_dir)
            shortlist = rank_and_shortlist(items, target_date=target_date, output_dir=output_dir)
        else:
            with open(shortlist_path, "r", encoding="utf-8") as f:
                shortlist_data = json.load(f)
            from src.common.models import SectionShortlist, ShortlistItem, RejectedItem
            sections = [
                SectionShortlist(
                    section_name=s["section_name"],
                    selected_items=[ShortlistItem(**i) for i in s.get("selected_items", [])],
                    target_item_count=s.get("target_item_count"),
                )
                for s in shortlist_data.get("sections", [])
            ]
            rejected = [RejectedItem(**r) for r in shortlist_data.get("rejected_items", [])]
            shortlist = Shortlist(
                generated_at=shortlist_data["generated_at"],
                date=shortlist_data.get("date"),
                sections=sections,
                rejected_items=rejected,
            )

        script = generate_script(shortlist, target_date=target_date, output_dir=output_dir)
        print(f"[pipeline] Script generated: ~{script.word_count_estimate} words.")
        if stage == "script":
            return

    # STAGE 4: TTS
    if stage in ("all", "tts"):
        script_path = os.path.join(output_dir, "script.json")
        if not os.path.exists(script_path):
            print(f"[pipeline] Error: script.json not found in {output_dir}")
            sys.exit(1)

        with open(script_path, "r", encoding="utf-8") as f:
            script_data = json.load(f)

        script_obj = Script(
            date=script_data["date"],
            title=script_data["title"],
            sections=[ScriptSection(**sec) for sec in script_data["sections"]],
            sources=script_data["sources"],
            word_count_estimate=script_data["word_count_estimate"],
            target_duration_seconds=script_data.get("target_duration_seconds"),
        )
        audio_meta = synthesize_briefing(script_obj, output_dir=output_dir, mock=True)
        print(f"[pipeline] TTS synthesis complete: {audio_meta['audio_path']}")
        if stage == "tts":
            return

    # STAGE 5: PUBLISH
    if stage in ("all", "publish"):
        script_path = os.path.join(output_dir, "script.json")
        audio_meta_path = os.path.join(output_dir, "audio_meta.json")
        if not os.path.exists(script_path) or not os.path.exists(audio_meta_path):
            print(f"[pipeline] Error: script.json or audio_meta.json missing in {output_dir}")
            sys.exit(1)

        with open(script_path, "r", encoding="utf-8") as f:
            script_data = json.load(f)
        with open(audio_meta_path, "r", encoding="utf-8") as f:
            audio_meta = json.load(f)

        script_obj = Script(
            date=script_data["date"],
            title=script_data["title"],
            sections=[ScriptSection(**sec) for sec in script_data["sections"]],
            sources=script_data["sources"],
            word_count_estimate=script_data["word_count_estimate"],
            target_duration_seconds=script_data.get("target_duration_seconds"),
        )
        report = publish_episode(audio_meta, script_obj, output_dir=output_dir)
        print(f"[pipeline] Publish complete: status={report['status']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Morning Brief Automation CLI")
    parser.add_argument(
        "--stage",
        choices=["all", "ingest", "rank", "script", "tts", "publish"],
        default="all",
        help="Pipeline stage to execute (default: all)",
    )
    parser.add_argument(
        "--date",
        default="",
        help="Target date for briefing in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--config",
        default="config/sources.yaml",
        help="Path to source configuration YAML file",
    )
    args = parser.parse_args()

    run_pipeline(stage=args.stage, target_date=args.date, config_path=args.config)


if __name__ == "__main__":
    main()
