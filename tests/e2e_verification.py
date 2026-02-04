import requests
import sys
import time
import uuid

BASE_URL = "http://localhost:8000/api"

def run_tests():
    print("Starting E2E Tests inside container...")
    
    # 1. Login
    print("1. Testing Admin Login...")
    login_data = {"username": "admin", "password": "admin"}
    r = None
    try:
        r = requests.post(f"{BASE_URL}/admin/login", data=login_data)
        r.raise_for_status()
        token = r.json()["access_token"]
        print(f"   Login Success. Token: {token[:10]}...")
    except Exception as e:
        print(f"   Login Failed: {e}")
        if r is not None:
            print(f"   Response: {r.text}")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Skill
    print("2. Testing Skill Creation...")
    skill_data = {
        "name": "Test Skill E2E",
        "slug": f"test-skill-e2e-{int(time.time())}",
        "description": "Created by E2E test",
        "content": "Test content",
        "category_slug": "chat", # Assumes 'chat' exists from seed
        "source_url": "http://test.com",
        "tags": ["test", "e2e"]
    }
    r = None
    try:
        r = requests.post(f"{BASE_URL}/admin/skills", json=skill_data, headers=headers)
        r.raise_for_status()
        skill_id = r.json()["id"]
        print(f"   Skill Created: {skill_id}")
    except Exception as e:
        print(f"   Skill Create Failed: {e}")
        if r is not None:
            print(f"   Response: {r.text}")
        sys.exit(1)

    # 3. Ingest Event
    print("3. Testing Event Ingestion...")
    event_data = {
        "type": "view",
        "skill_id": skill_id,
        "session_id": str(uuid.uuid4()),
        "context": '{"source": "e2e"}'
    }
    r = None
    try:
        # app/api/events.py endpoint for view is /events/view
        r = requests.post(f"{BASE_URL}/events/view", json=event_data)
        r.raise_for_status()
        print("   Event Recorded.")
    except Exception as e:
        print(f"   Event Failed: {e}")
        if r is not None:
            print(f"   Response: {r.text}")
        sys.exit(1)

    # 4. Rankings
    print("4. Testing Rankings...")
    r = None
    try:
        r = requests.get(f"{BASE_URL}/rankings/top10")
        r.raise_for_status()
        items = r.json()
        print(f"   Rankings Retrieved. Items: {len(items)}")
    except Exception as e:
        print(f"   Rankings Failed: {e}")
        if r is not None:
            print(f"   Response: {r.text}")
        sys.exit(1)

    print("ALL TESTS PASSED")

if __name__ == "__main__":
    run_tests()
