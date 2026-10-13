# Ranking and Shortlist Module (`src/rank`)

## Responsibility
Scores, deduplicates, and filters ingested news items, allocating the top-priority stories into designated episode sections while recording rejected candidates with explicit reasons.

## Expected Interfaces
- `rank_and_shortlist(items: List[NewsItem], target_date: Optional[str] = None, output_dir: Optional[str] = None) -> Shortlist`:
  - **Inputs**: List of normalized `NewsItem` objects, target episode date, optional output directory.
  - **Outputs**: `Shortlist` domain object complying with `schemas/shortlist.schema.json`.
  - **Artifacts**: Writes `data/{YYYY-MM-DD}/shortlist.json`.
- **Sections Handled**:
  - `markets`: Markets snapshot (target ~70s)
  - `fed_bsp`: Fed and BSP policy updates (target ~70s)
  - `big_tech`: Big Tech headlines (target ~80s)
  - `philippines`: One-minute Philippines focus (target ~60s)
  - `india`: One-minute India focus (target ~60s)
  - `world_news`: World news roundup (target ~80s)
