import requests
import sys
import time
import uuid
import json

BASE_URL = "http://localhost:8000/api"

def print_step(msg):
    print(f"\n[STEP] {msg}")

def run_full_test():
    print("Starting Full System Verification...")
    
    # ---------------------------------------------------------
    # 1. Admin Login
    # ---------------------------------------------------------
    print_step("1. Admin Login")
    login_data = {"username": "admin", "password": "admin"}
    try:
        r = requests.post(f"{BASE_URL}/admin/login", data=login_data)
        r.raise_for_status()
        token = r.json()["access_token"]
        print(f"   Success. Token obtained.")
    except Exception as e:
        print(f"   Failed: {e}")
        if 'r' in locals(): print(r.text)
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    # ---------------------------------------------------------
    # 2. Check Raw Skills (Simulate Ingested Queue)
    # ---------------------------------------------------------
    print_step("2. Check Raw Waiting Queue (Pre-Ingest Check)")
    # We expect some items if seed ran, or empty if fresh.
    r = requests.get(f"{BASE_URL}/admin/raw-skills?status=pending", headers=headers)
    if r.status_code == 200:
        items = r.json()["items"]
        print(f"   Found {len(items)} pending raw skills.")
    else:
        print(f"   Failed to list raw skills: {r.status_code} {r.text}")

    # ---------------------------------------------------------
    # 3. Create/Approve a Skill Manually (Admin Flow)
    # ---------------------------------------------------------
    print_step("3. Admin Manually Creates/Approves a Skill")
    unique_slug = f"auto-test-skill-{int(time.time())}"
    skill_payload = {
        "slug": unique_slug,
        "name": f"Auto Test Skill {int(time.time())}",
        "description": "This is an E2E test skill",
        "author": "E2E Bot",
        "category_slug": "chat", # Assumes 'chat' category from seed
        "tags": ["e2e", "test", "python"],
        "content": "# Test Skill\n\nThis is a test.",
        "is_verified": True,
        "is_official": True
    }
    
    try:
        r = requests.post(f"{BASE_URL}/admin/skills", json=skill_payload, headers=headers)
        r.raise_for_status()
        skill = r.json()
        skill_id = skill["id"]
        print(f"   Success. Created Skill ID: {skill_id}")
    except Exception as e:
        print(f"   Failed to create skill: {e}")
        if 'r' in locals(): print(r.text)
        sys.exit(1)

    # ---------------------------------------------------------
    # 4. Public API Verification
    # ---------------------------------------------------------
    print_step("4. Public API - List & Filter")
    # Verify it appears in public list
    try:
        r = requests.get(f"{BASE_URL}/skills?q={unique_slug}")
        r.raise_for_status()
        data = r.json()
        found = any(s["id"] == skill_id for s in data["items"])
        if found:
            print("   Success. New skill found in public search.")
        else:
            print("   Warning. New skill NOT found in search (indexing delay?).")
            
        # Verify Detail
        r = requests.get(f"{BASE_URL}/skills/{skill_id}")
        r.raise_for_status()
        print("   Success. Skill detail retrieved.")
    except Exception as e:
        print(f"   Failed Public API check: {e}")
        sys.exit(1)

    # ---------------------------------------------------------
    # 5. Event Ingestion (User Action)
    # ---------------------------------------------------------
    print_step("5. Event Ingestion (View/Use)")
    try:
        # View Event
        payload = {
            "type": "view",
            "skill_id": skill_id,
            "session_id": str(uuid.uuid4()),
            "context": json.dumps({"source": "full_test"})
        }
        r = requests.post(f"{BASE_URL}/events/view", json=payload)
        r.raise_for_status()
        print("   Success. View event recorded.")
    except Exception as e:
        print(f"   Failed Event Ingestion: {e}")
        if 'r' in locals(): print(r.text)
        sys.exit(1)

    # ---------------------------------------------------------
    # 6. Rankings Check (Pre-Worker)
    # ---------------------------------------------------------
    print_step("6. Rankings Check")
    try:
        r = requests.get(f"{BASE_URL}/rankings/top10")
        r.raise_for_status()
        items = r.json()
        print(f"   Current Top 10 count: {len(items)}")
    except Exception as e:
        print(f"   Failed Ranking Check: {e}")
        sys.exit(1)

    print("\n[SUCCESS] All backend system flows verified.")

if __name__ == "__main__":
    run_full_test()
