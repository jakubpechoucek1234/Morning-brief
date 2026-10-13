# Podcast Publishing Module (`src/publish`)

## Responsibility
Packages the finalized audio episode, updates the private podcast RSS feed (`podcast.xml`), handles remote asset publishing (e.g. AWS S3 / Cloudflare R2 bucket), and generates a run health summary.

## Expected Interfaces
- `publish_episode(audio_meta: Dict[str, Any], script: Script, config: Optional[Dict[str, Any]] = None, output_dir: Optional[str] = None) -> Dict[str, Any]`:
  - **Inputs**: Synthesized audio metadata (`audio_meta`), episode `Script` object, optional publishing config, and destination directory.
  - **Outputs**: Publication status dictionary containing enclosure URL, feed file path, and run report.
  - **Artifacts**: Writes `data/{YYYY-MM-DD}/podcast.xml` and `data/{YYYY-MM-DD}/run_report.json`.
- Feed Features:
  - Valid RSS 2.0 with iTunes podcast tags (`itunes:duration`, `itunes:explicit`, `itunes:episodeType`).
  - `<enclosure>` tag pointing to private audio hosting URL.
  - Tokenized or unguessable feed URL support for private distribution.
