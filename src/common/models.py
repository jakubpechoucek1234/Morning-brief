"""Core data models for Morning Brief pipeline stages."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SourceConfig:
    """Configuration for an ingestion source."""
    name: str
    type: str  # rss | api | web
    url: str
    region: str
    topic: str
    priority: int
    poll_window_hours: int


@dataclass
class NewsItem:
    """Canonical normalized news item across all ingestion channels."""
    id: str
    headline: str
    summary: str
    source: str
    url: str
    region: str
    topic: str
    published_at: str
    raw_payload: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data.get("raw_payload") is None:
            data.pop("raw_payload", None)
        return data


@dataclass
class ShortlistItem:
    """News item shortlisted for episode inclusion."""
    id: str
    headline: str
    summary: str
    source: str
    url: str
    score: float
    published_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RejectedItem:
    """Item filtered out during deduplication or ranking."""
    headline: str
    source: str
    reason: str
    id: Optional[str] = None
    url: Optional[str] = None
    stage: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class SectionShortlist:
    """Shortlisted items allocated to a specific episode section."""
    section_name: str
    selected_items: List[ShortlistItem] = field(default_factory=list)
    target_item_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "section_name": self.section_name,
            "selected_items": [item.to_dict() for item in self.selected_items],
        }
        if self.target_item_count is not None:
            data["target_item_count"] = self.target_item_count
        return data


@dataclass
class Shortlist:
    """Shortlist artifact conforming to schemas/shortlist.schema.json."""
    generated_at: str
    sections: List[SectionShortlist]
    rejected_items: List[RejectedItem] = field(default_factory=list)
    date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "generated_at": self.generated_at,
            "sections": [s.to_dict() for s in self.sections],
            "rejected_items": [r.to_dict() for r in self.rejected_items],
        }
        if self.date is not None:
            data["date"] = self.date
        return data


@dataclass
class ScriptSection:
    """Section text and duration target in the briefing script."""
    name: str
    duration_target_seconds: int
    text: str
    items: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Script:
    """Episode narration script conforming to schemas/script.schema.json."""
    date: str
    title: str
    sections: List[ScriptSection]
    sources: List[str]
    word_count_estimate: int
    target_duration_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "date": self.date,
            "title": self.title,
            "sections": [s.to_dict() for s in self.sections],
            "sources": self.sources,
            "word_count_estimate": self.word_count_estimate,
        }
        if self.target_duration_seconds is not None:
            data["target_duration_seconds"] = self.target_duration_seconds
        return data
