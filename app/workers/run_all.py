"""Run all workers."""

import asyncio
from app.workers import ingest_and_parse, compute_popularity, build_rank_snapshots

async def main():
    while True:
        print("--- Starting Workers ---")
        try:
            await ingest_and_parse.run()
            await compute_popularity.run()
            await build_rank_snapshots.run()
        except Exception as e:
            print(f"Worker Error: {e}")
        print("--- Workers Finished. Sleeping for 60s ---")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
