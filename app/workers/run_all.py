"""Run all workers."""

import asyncio
from datetime import datetime, timedelta, timezone

from app.workers import ingest_and_parse, compute_popularity, build_rank_snapshots
from app.db.session import AsyncSessionLocal
from app.repos.system_setting_repo import (
    DEFAULT_WORKER_SETTINGS,
    get_worker_settings,
    get_worker_status_value,
    set_worker_status_value,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _patch_worker_status(patch: dict) -> None:
    """Best-effort: write worker heartbeat to DB (never crash worker loop)."""
    try:
        async with AsyncSessionLocal() as db:
            current = await get_worker_status_value(db)
            current_dict = current if isinstance(current, dict) else {}
            merged = current_dict | patch
            now = _utc_now_iso()
            merged["heartbeat_at"] = now

            # Keep a bounded event log for quick debugging in the admin UI.
            prev_phase = current_dict.get("phase")
            next_phase = merged.get("phase")
            has_error = bool(patch.get("last_error") or patch.get("ingest_last_source_error"))
            phase_changed = ("phase" in patch) and (next_phase != prev_phase)
            if phase_changed or has_error:
                events = merged.get("recent_events")
                if not isinstance(events, list):
                    events = []
                event = {"at": now, "phase": next_phase or "unknown"}
                for key in (
                    "ingest_source_id",
                    "ingest_source_type",
                    "ingest_source_index",
                    "ingest_source_total",
                    "ingest_directory_url",
                    "ingest_repo_full_name",
                    "ingest_last_source_error",
                    "last_error",
                ):
                    value = merged.get(key)
                    if value is not None and value != "":
                        event[key] = value
                events.append(event)
                merged["recent_events"] = events[-50:]

            await set_worker_status_value(db, merged)
            await db.commit()
    except Exception:
        return

async def main():
    while True:
        print("--- Starting Workers ---")
        worker_settings = DEFAULT_WORKER_SETTINGS
        try:
            # Load runtime settings from DB (falls back to defaults if unavailable).
            try:
                async with AsyncSessionLocal() as db:
                    worker_settings = await get_worker_settings(db)
            except Exception:
                worker_settings = DEFAULT_WORKER_SETTINGS

            loop_started_at = _utc_now_iso()
            interval = int(getattr(worker_settings, "auto_ingest_interval_seconds", 60) or 60)

            # When ingest is disabled, clear stale ingest progress fields to avoid confusing UI.
            clear_ingest_progress = {}
            if not bool(getattr(worker_settings, "auto_ingest_enabled", True)):
                clear_ingest_progress = {
                    "ingest_source_id": None,
                    "ingest_source_type": None,
                    "ingest_source_index": None,
                    "ingest_source_total": None,
                    "ingest_url": None,
                    "ingest_directory_url": None,
                    "ingest_repo_full_name": None,
                    "ingest_discovered_repo_index": None,
                    "ingest_discovered_repo_total": None,
                    "ingest_discovered_repos": None,
                    "ingest_last_source_error": None,
                    "ingested_so_far": None,
                    "ingest_results": None,
                    "last_ingested_raw_items": None,
                }

            await _patch_worker_status(
                {
                    "phase": "loop_start",
                    "loop_started_at": loop_started_at,
                    "auto_ingest_enabled": bool(getattr(worker_settings, "auto_ingest_enabled", True)),
                    "interval_seconds": interval,
                    "last_error": None,
                    **clear_ingest_progress,
                }
            )

            if worker_settings.auto_ingest_enabled:
                await _patch_worker_status({"phase": "ingest_and_parse"})
                stats = await ingest_and_parse.run()
                ingested = None
                pending_before = None
                pending_after = None
                processed = None
                errors = None
                if isinstance(stats, dict):
                    ingested = stats.get("ingested")
                    parse_stats = stats.get("parse") if isinstance(stats.get("parse"), dict) else {}
                    pending_before = parse_stats.get("pending_before")
                    pending_after = parse_stats.get("pending_after")
                    processed = parse_stats.get("processed")
                    errors = parse_stats.get("errors")
                    drained = parse_stats.get("drained")
                await _patch_worker_status(
                    {
                        "phase": "ingest_and_parse_done",
                        "last_ingested_raw_items": int(ingested) if isinstance(ingested, int) else None,
                        "last_pending_before": int(pending_before) if isinstance(pending_before, int) else None,
                        "last_pending_after": int(pending_after) if isinstance(pending_after, int) else None,
                        "last_processed_in_loop": int(processed) if isinstance(processed, int) else None,
                        "last_error_count_in_loop": int(errors) if isinstance(errors, int) else None,
                        "last_drained_in_loop": int(drained) if isinstance(drained, int) else None,
                    }
                )
            else:
                # Important: allow draining the pending parse queue even when crawl/ingest is paused.
                # Otherwise the admin toggle "OFF" would freeze the backlog permanently.
                print("Auto ingest disabled. Skipping crawl/ingest; parsing pending queue only.")
                await _patch_worker_status({"phase": "parse_only", **clear_ingest_progress})
                pending_before = None
                pending_after = None
                processed = None
                errors = None
                drained_total = 0
                try:
                    async with AsyncSessionLocal() as db:
                        # Drain the queue in one loop run (no "sleep between loops"),
                        # so admins see progress immediately after a re-queue.
                        while True:
                            parse_stats = await ingest_and_parse.parse_queued_raw_skills(db)
                            if not isinstance(parse_stats, dict):
                                break
                            pending_before = parse_stats.get("pending_before")
                            pending_after = parse_stats.get("pending_after")
                            processed = parse_stats.get("processed")
                            errors = parse_stats.get("errors")
                            drained = parse_stats.get("drained")
                            if isinstance(drained, int):
                                drained_total += drained
                            # Stop when there's nothing left (or no progress).
                            if not isinstance(pending_after, int) or pending_after <= 0:
                                break
                            if isinstance(drained, int) and drained <= 0:
                                break
                except Exception as e:
                    await _patch_worker_status({"phase": "parse_only_error", "last_error": str(e)})
                await _patch_worker_status(
                    {
                        "phase": "parse_only_done",
                        "last_pending_before": int(pending_before) if isinstance(pending_before, int) else None,
                        "last_pending_after": int(pending_after) if isinstance(pending_after, int) else None,
                        "last_processed_in_loop": int(processed) if isinstance(processed, int) else None,
                        "last_error_count_in_loop": int(errors) if isinstance(errors, int) else None,
                        "last_drained_in_loop": int(drained_total),
                    }
                )

                # Even when crawl/ingest is OFF, we can still backfill GLM-generated summaries
                # for existing Skills in small batches. This avoids the common "GLM never runs"
                # perception when ingest is paused.
                try:
                    await _patch_worker_status({"phase": "glm_backfill_summaries"})
                    async with AsyncSessionLocal() as db:
                        await ingest_and_parse.backfill_missing_summaries(db, limit=10)
                        await ingest_and_parse.backfill_missing_detail_overviews(db, limit=5)
                except Exception as e:
                    await _patch_worker_status({"phase": "glm_backfill_error", "last_error": str(e)})

                # Embeddings backfill even when ingest OFF
                try:
                    await _patch_worker_status({"phase": "embedding_backfill"})
                    async with AsyncSessionLocal() as db:
                        await ingest_and_parse.backfill_missing_embeddings(db, limit=20)
                except Exception as e:
                    await _patch_worker_status({"phase": "embedding_backfill_error", "last_error": str(e)})

            await _patch_worker_status({"phase": "compute_popularity"})
            await compute_popularity.run()
            await _patch_worker_status({"phase": "build_rank_snapshots"})
            await build_rank_snapshots.run()
        except Exception as e:
            print(f"Worker Error: {e}")
            await _patch_worker_status({"phase": "error", "last_error": str(e)})
        interval = int(getattr(worker_settings, "auto_ingest_interval_seconds", 60) or 60)
        loop_finished_at = _utc_now_iso()
        try:
            next_run = (datetime.now(timezone.utc) + timedelta(seconds=interval)).isoformat()
        except Exception:
            next_run = None
        await _patch_worker_status(
            {
                "phase": "sleep",
                "loop_finished_at": loop_finished_at,
                "next_run_at": next_run,
            }
        )
        print(f"--- Workers Finished. Sleeping for {interval}s ---")
        await asyncio.sleep(interval)

if __name__ == "__main__":
    asyncio.run(main())
