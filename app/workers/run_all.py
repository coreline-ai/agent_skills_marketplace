"""Run all workers."""

import asyncio
from app.workers import ingest_and_parse, compute_popularity, build_rank_snapshots
from app.db.session import AsyncSessionLocal
from app.repos.system_setting_repo import DEFAULT_WORKER_SETTINGS, get_worker_settings

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

            if worker_settings.auto_ingest_enabled:
                await ingest_and_parse.run()
            else:
                print("Auto ingest disabled. Skipping crawl/ingest.")

            await compute_popularity.run()
            await build_rank_snapshots.run()
        except Exception as e:
            print(f"Worker Error: {e}")
        interval = int(getattr(worker_settings, "auto_ingest_interval_seconds", 60) or 60)
        print(f"--- Workers Finished. Sleeping for {interval}s ---")
        await asyncio.sleep(interval)

if __name__ == "__main__":
    asyncio.run(main())
