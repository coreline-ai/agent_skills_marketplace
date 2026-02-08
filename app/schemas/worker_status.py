"""Worker status schema (heartbeat for observability)."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class WorkerStatus(BaseModel):
    """Lightweight worker heartbeat stored in system_settings.value."""

    phase: str = Field(default="unknown")
    heartbeat_at: Optional[str] = None  # ISO8601

    loop_started_at: Optional[str] = None  # ISO8601
    loop_finished_at: Optional[str] = None  # ISO8601
    next_run_at: Optional[str] = None  # ISO8601

    auto_ingest_enabled: Optional[bool] = None
    interval_seconds: Optional[int] = None

    last_ingested_raw_items: Optional[int] = None
    last_pending_before: Optional[int] = None
    last_pending_after: Optional[int] = None
    last_processed_in_loop: Optional[int] = None
    last_error_count_in_loop: Optional[int] = None
    last_drained_in_loop: Optional[int] = None

    last_error: Optional[str] = None

    # Ingest source progress (best-effort)
    ingest_source_id: Optional[str] = None
    ingest_source_type: Optional[str] = None
    ingest_source_index: Optional[int] = None
    ingest_source_total: Optional[int] = None
    ingest_url: Optional[str] = None
    ingest_directory_url: Optional[str] = None
    ingest_repo_full_name: Optional[str] = None
    ingest_discovered_repo_index: Optional[int] = None
    ingest_discovered_repo_total: Optional[int] = None
    ingest_discovered_repos: Optional[int] = None
    ingest_last_source_error: Optional[str] = None
    ingested_so_far: Optional[int] = None
    ingest_results: Optional[int] = None

    # Bounded event log (last ~50 phase transitions + errors)
    recent_events: Optional[list[dict]] = None
