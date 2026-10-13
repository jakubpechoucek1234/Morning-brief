# Script Generation Module (`src/script`)

## Responsibility
Transforms the daily news shortlist into a structured, spoken-audio script conforming to the timing budget (~420–480 seconds at ~150 words per minute) and format requirements.

## Timing Budget Allocation
- **Markets Snapshot**: 70 seconds (~175 words)
- **Fed & BSP Policy**: 70 seconds (~175 words)
- **Big Tech Headlines**: 80 seconds (~200 words)
- **Philippines Focus**: 60 seconds (~150 words)
- **India Focus**: 60 seconds (~150 words)
- **World News Roundup**: 80 seconds (~200 words)
- **Total Budget**: 420 seconds (~1,050 words)

## Expected Interfaces
- `generate_script(shortlist: Shortlist, target_date: Optional[str] = None, output_dir: Optional[str] = None) -> Script`:
  - **Inputs**: `Shortlist` domain object, optional target date and output directory.
  - **Outputs**: `Script` domain object matching `schemas/script.schema.json`.
  - **Artifacts**: Writes `data/{YYYY-MM-DD}/script.json` and `data/{YYYY-MM-DD}/script.txt`.
