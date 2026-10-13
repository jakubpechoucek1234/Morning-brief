"""Audio synthesis adapters and pipeline entrypoint."""

import hashlib
import json
import os
from typing import Any, Dict, Optional

from src.common.models import Script


def create_mock_mp3(filepath: str) -> int:
    """Create a minimal mock MP3 file for local testing and CI/CD pipelines."""
    # Minimal MPEG frame header (sync word 0xFFFB)
    mock_payload = b"\xff\xfb\x90\x64" + (b"\x00" * 4096)
    with open(filepath, "wb") as f:
        f.write(mock_payload)
    return len(mock_payload)


def synthesize_briefing(
    script: Script,
    output_dir: Optional[str] = None,
    mock: bool = True,
) -> Dict[str, Any]:
    """Synthesize episode script into an audio file.

    In scaffold mode or when mock=True, generates a lightweight mock MP3 file
    and emits audio metadata required by the publisher.
    """
    date_str = script.date
    if not output_dir:
        output_dir = os.path.join("data", date_str)

    os.makedirs(output_dir, exist_ok=True)
    audio_path = os.path.join(output_dir, f"morning-brief-{date_str}.mp3")

    if mock or not os.getenv("ELEVENLABS_API_KEY"):
        print(f"[tts] Running in mock/scaffold mode. Generating audio placeholder at {audio_path}")
        size_bytes = create_mock_mp3(audio_path)
    else:
        # TODO: Implement production ElevenLabs / OpenAI TTS provider call
        print("[tts] Production TTS adapter invoked (placeholder)")
        size_bytes = create_mock_mp3(audio_path)

    # Compute SHA256
    with open(audio_path, "rb") as f:
        file_sha256 = hashlib.sha256(f.read()).hexdigest()

    # Duration estimate: ~150 words per minute -> 2.5 words per second
    estimated_duration = max(int(script.word_count_estimate / 2.5), 420)

    metadata: Dict[str, Any] = {
        "audio_path": audio_path,
        "filename": os.path.basename(audio_path),
        "duration_seconds": estimated_duration,
        "file_size_bytes": size_bytes,
        "sha256": file_sha256,
        "content_type": "audio/mpeg",
    }

    meta_path = os.path.join(output_dir, "audio_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"[tts] Audio synthesis complete: {audio_path} ({metadata['duration_seconds']}s, {size_bytes} bytes)")
    return metadata
