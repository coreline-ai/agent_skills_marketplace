import asyncio
from app.db.session import AsyncSessionLocal
from app.llm.embeddings import generate_embedding
from sqlalchemy import text

async def verify():
    print("Verifying Vector Search...")
    
    # 1. Check DB Extension
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            if result.scalar():
                print("✅ pgvector extension is installed.")
            else:
                print("❌ pgvector extension is MISSING!")
        except Exception as e:
            print(f"❌ Error checking extension: {e}")

        # 2. Check Embeddings Generation
        query = "agent framework"
        print(f"Generating embedding for '{query}'...")
        vec = generate_embedding(query)
        if vec and len(vec) == 384:
            print("✅ Embedding generation works (dim=384).")
        else:
            print(f"❌ Embedding generation failed or wrong dimension: {len(vec) if vec else 'None'}")

        # 3. Check Backfill Status
        try:
            result = await db.execute(text("SELECT count(*) FROM skills WHERE embedding IS NOT NULL"))
            count = result.scalar()
            print(f"ℹ️  Skills with embeddings: {count}")
        except Exception as e:
            print(f"❌ Error checking skills: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
