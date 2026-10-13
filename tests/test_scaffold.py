"""Validation test suite for Morning Brief scaffold."""

import json
import os
import tempfile
import xml.etree.ElementTree as ET
import pytest
import yaml
from jsonschema import Draft7Validator

from src.ingest.ingester import load_sources_config
from src.main import run_pipeline


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_sources_configuration():
    """Validate config/sources.yaml schema, source count, topics, and field types."""
    sources_path = os.path.join(REPO_ROOT, "config", "sources.yaml")
    assert os.path.exists(sources_path), "config/sources.yaml must exist"

    with open(sources_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "sources" in data, "config/sources.yaml must contain 'sources' key"
    sources = data["sources"]

    # Must have 8-12 starter sources
    assert 8 <= len(sources) <= 12, f"Expected 8-12 sources, got {len(sources)}"

    required_fields = ["name", "type", "url", "region", "topic", "priority", "poll_window_hours"]
    expected_topics = {"markets", "central_bank", "big_tech", "philippines_focus", "india_focus", "world_news"}
    found_topics = set()

    for idx, s in enumerate(sources):
        for field in required_fields:
            assert field in s, f"Source #{idx} missing required field: {field}"

        assert s["type"] in ("rss", "api", "web"), f"Invalid source type: {s['type']}"
        assert isinstance(s["priority"], int), f"Priority must be an integer: {s['priority']}"
        assert isinstance(s["poll_window_hours"], int), f"poll_window_hours must be an integer: {s['poll_window_hours']}"
        assert s["url"].startswith("http"), f"URL must be HTTP/HTTPS: {s['url']}"
        found_topics.add(s["topic"])

    # Must cover all 6 required topics
    assert expected_topics.issubset(found_topics), f"Missing topics: {expected_topics - found_topics}"


def test_json_schemas_validity():
    """Verify that both script and shortlist schemas are valid JSON schemas."""
    schema_dir = os.path.join(REPO_ROOT, "schemas")
    for schema_file in ["script.schema.json", "shortlist.schema.json"]:
        path = os.path.join(schema_dir, schema_file)
        assert os.path.exists(path), f"Schema {schema_file} missing"
        with open(path, "r", encoding="utf-8") as f:
            schema_data = json.load(f)
        # Check against draft 7 validator
        Draft7Validator.check_schema(schema_data)


def test_pipeline_scaffold_output_and_schema_conformance():
    """Run pipeline end-to-end and ensure output validates against JSON schemas."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_date = "2026-10-13"
        out_dir = os.path.join(tmpdir, "data", test_date)

        # Ingest
        from src.ingest import ingest_sources
        items = ingest_sources(output_dir=out_dir)
        assert os.path.exists(os.path.join(out_dir, "raw_items.json"))

        # Rank
        from src.rank import rank_and_shortlist
        shortlist = rank_and_shortlist(items, target_date=test_date, output_dir=out_dir)
        shortlist_path = os.path.join(out_dir, "shortlist.json")
        assert os.path.exists(shortlist_path)

        # Validate shortlist against schemas/shortlist.schema.json
        shortlist_schema_path = os.path.join(REPO_ROOT, "schemas", "shortlist.schema.json")
        with open(shortlist_schema_path, "r", encoding="utf-8") as f:
            shortlist_schema = json.load(f)
        with open(shortlist_path, "r", encoding="utf-8") as f:
            shortlist_data = json.load(f)
        Draft7Validator(shortlist_schema).validate(shortlist_data)

        # Script
        from src.script import generate_script
        script = generate_script(shortlist, target_date=test_date, output_dir=out_dir)
        script_path = os.path.join(out_dir, "script.json")
        assert os.path.exists(script_path)
        assert os.path.exists(os.path.join(out_dir, "script.txt"))

        # Validate script against schemas/script.schema.json
        script_schema_path = os.path.join(REPO_ROOT, "schemas", "script.schema.json")
        with open(script_schema_path, "r", encoding="utf-8") as f:
            script_schema = json.load(f)
        with open(script_path, "r", encoding="utf-8") as f:
            script_data = json.load(f)
        Draft7Validator(script_schema).validate(script_data)

        # TTS
        from src.tts import synthesize_briefing
        audio_meta = synthesize_briefing(script, output_dir=out_dir, mock=True)
        assert os.path.exists(audio_meta["audio_path"])
        assert os.path.exists(os.path.join(out_dir, "audio_meta.json"))

        # Publish
        from src.publish import publish_episode
        report = publish_episode(audio_meta, script, output_dir=out_dir)
        podcast_xml_path = os.path.join(out_dir, "podcast.xml")
        assert os.path.exists(podcast_xml_path)
        assert os.path.exists(os.path.join(out_dir, "run_report.json"))

        # Check RSS XML parses without error
        tree = ET.parse(podcast_xml_path)
        root = tree.getroot()
        assert root.tag == "rss"
        channel = root.find("channel")
        assert channel is not None
        assert channel.find("item") is not None


def test_github_workflow_syntax():
    """Verify that .github/workflows/daily-brief.yml is valid YAML and includes required triggers."""
    workflow_path = os.path.join(REPO_ROOT, ".github", "workflows", "daily-brief.yml")
    assert os.path.exists(workflow_path)

    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = yaml.safe_load(f)

    # Workflow triggers
    # Note: in YAML, on: can be parsed as True/False boolean key if not quoted, or as string 'on'
    on_trigger = workflow.get("on") or workflow.get(True)
    assert on_trigger is not None, "Workflow must have triggers defined"
    assert "schedule" in on_trigger, "Workflow must include schedule cron trigger"
    assert "workflow_dispatch" in on_trigger, "Workflow must include manual workflow_dispatch trigger"

    # Jobs
    assert "jobs" in workflow
    job = next(iter(workflow["jobs"].values()))
    step_names_lower = [step.get("name", "").lower() for step in job.get("steps", [])]
    assert any("ingest" in name for name in step_names_lower)
    assert any("rank" in name for name in step_names_lower)
    assert any("script" in name for name in step_names_lower)
    assert any("audio" in name or "tts" in name for name in step_names_lower)
    assert any("publish" in name for name in step_names_lower)
    assert any("upload" in name or "artifact" in name for name in step_names_lower)


def test_module_readmes_exist():
    """Ensure all required module folders have README notes."""
    required_dirs = [
        "src/ingest",
        "src/rank",
        "src/script",
        "src/tts",
        "src/publish",
        "src/common",
    ]
    for d in required_dirs:
        readme_path = os.path.join(REPO_ROOT, d, "README.md")
        assert os.path.exists(readme_path), f"README.md missing in {d}"
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert len(content.strip()) > 50, f"README.md in {d} is too brief"
        assert "Responsibility" in content or "responsibility" in content.lower()
