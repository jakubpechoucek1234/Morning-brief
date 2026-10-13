# TTS Narration Module (`src/tts`)

## Responsibility
Renders the generated script text into podcast-grade audio (MP3/M4A). It interfaces with TTS providers (e.g., ElevenLabs, OpenAI Audio API, or local mock for offline CI/CD) and computes duration, byte size, and audio checksums.

## Expected Interfaces
- `synthesize_briefing(script: Script, output_dir: Optional[str] = None, mock: bool = True) -> Dict[str, Any]`:
  - **Inputs**: `Script` domain object, destination directory, mock flag.
  - **Outputs**: Dictionary with audio metadata:
    - `audio_path`: Local path to synthesized MP3 file.
    - `duration_seconds`: Actual or estimated audio length in seconds.
    - `file_size_bytes`: Size in bytes.
    - `sha256`: SHA-256 integrity hash of the audio artifact.
  - **Artifacts**: Writes `data/{YYYY-MM-DD}/morning-brief-{date}.mp3` and `data/{YYYY-MM-DD}/audio_meta.json`.
- Pluggable Provider Adapters:
  - `MockTTSAdapter`: Used in CI and testing without external API calls.
  - `ElevenLabsAdapter`: High-fidelity voice synthesis (requires `ELEVENLABS_API_KEY`).
  - `OpenAITTSAdapter`: Fast neural voice synthesis (requires `OPENAI_API_KEY`).
