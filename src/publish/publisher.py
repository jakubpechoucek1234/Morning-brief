"""Podcast feed generator and episode publisher."""

import datetime
import json
import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional

from src.common.models import Script


def generate_podcast_rss(
    episodes: list,
    feed_title: str = "Morning Brief",
    feed_description: str = "Daily 7-8 minute private audio news briefing",
    feed_link: str = "https://morningbrief.local",
) -> str:
    """Generate RSS 2.0 XML with iTunes podcast extensions."""
    rss = ET.Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
            "xmlns:content": "http://purl.org/rss/1.0/modules/content/",
        },
    )
    channel = ET.SubElement(rss, "channel")

    title_elem = ET.SubElement(channel, "title")
    title_elem.text = feed_title
    desc_elem = ET.SubElement(channel, "description")
    desc_elem.text = feed_description
    link_elem = ET.SubElement(channel, "link")
    link_elem.text = feed_link

    itunes_author = ET.SubElement(channel, "itunes:author")
    itunes_author.text = "Morning Brief"
    itunes_explicit = ET.SubElement(channel, "itunes:explicit")
    itunes_explicit.text = "false"

    for ep in episodes:
        item = ET.SubElement(channel, "item")
        i_title = ET.SubElement(item, "title")
        i_title.text = ep.get("title", "Morning Brief Episode")
        i_desc = ET.SubElement(item, "description")
        i_desc.text = ep.get("description", "")
        i_pub_date = ET.SubElement(item, "pubDate")
        i_pub_date.text = ep.get("pub_date", datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000"))
        i_guid = ET.SubElement(item, "guid", {"isPermaLink": "false"})
        i_guid.text = ep.get("guid", ep.get("enclosure_url", ""))

        enclosure = ET.SubElement(
            item,
            "enclosure",
            {
                "url": ep.get("enclosure_url", ""),
                "length": str(ep.get("file_size_bytes", 0)),
                "type": "audio/mpeg",
            },
        )
        i_dur = ET.SubElement(item, "itunes:duration")
        i_dur.text = str(ep.get("duration_seconds", 450))

    return ET.tostring(rss, encoding="utf-8", xml_declaration=True).decode("utf-8")


def publish_episode(
    audio_meta: Dict[str, Any],
    script: Script,
    config: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Publish episode metadata, generate RSS feed, and emit run report."""
    date_str = script.date
    if not output_dir:
        output_dir = os.path.join("data", date_str)

    os.makedirs(output_dir, exist_ok=True)
    base_url = (config or {}).get("base_url", "https://storage.example.com/morning-brief")
    audio_filename = audio_meta.get("filename", f"morning-brief-{date_str}.mp3")
    enclosure_url = f"{base_url}/{audio_filename}"

    episode_entry = {
        "title": script.title,
        "description": f"Daily briefing for {date_str} covering markets, Fed/BSP policy, Big Tech, Philippines, India, and world news.",
        "enclosure_url": enclosure_url,
        "file_size_bytes": audio_meta.get("file_size_bytes", 0),
        "duration_seconds": audio_meta.get("duration_seconds", 450),
        "guid": f"morning-brief-{date_str}",
        "pub_date": datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000"),
    }

    rss_xml = generate_podcast_rss([episode_entry])
    rss_path = os.path.join(output_dir, "podcast.xml")
    with open(rss_path, "w", encoding="utf-8") as f:
        f.write(rss_xml)

    # TODO: Upload audio_path and podcast.xml to remote storage bucket (e.g. AWS S3 / Cloudflare R2)
    # when credentials are provided in production environment.

    run_report: Dict[str, Any] = {
        "date": date_str,
        "status": "success",
        "published_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "title": script.title,
        "sections_count": len(script.sections),
        "sources_count": len(script.sources),
        "word_count_estimate": script.word_count_estimate,
        "target_duration_seconds": script.target_duration_seconds,
        "audio": audio_meta,
        "feed_path": rss_path,
        "enclosure_url": enclosure_url,
    }

    report_path = os.path.join(output_dir, "run_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(run_report, f, indent=2)

    print(f"[publish] Feed generated at {rss_path}")
    print(f"[publish] Run report written to {report_path}")

    return run_report
