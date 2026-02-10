#!/bin/sh
set -e

echo "Starting deployment scripts..."

# Connectivity check (Debug)
echo "Checking database connectivity..."
# Simple python script to test connection and log details
python3 <<EOF
import socket
import sys
import os
from urllib.parse import urlparse

db_url = os.environ.get('DATABASE_URL', '')
if not db_url:
    print("DATABASE_URL not set")
    sys.exit(0)

try:
    # Handle both postgresql:// and postgresql+asyncpg://
    url = urlparse(db_url.replace('postgresql+asyncpg://', 'postgresql://'))
    host = url.hostname
    port = url.port or 5432
    
    print(f"Testing connection to {host}:{port}...")
    
    # Try DNS resolution
    try:
        ais = socket.getaddrinfo(host, port)
        print(f"DNS resolved to: {[ai[4][0] for ai in ais]}")
    except Exception as e:
        print(f"DNS Resolution failed: {e}")
        
    # Try socket connection
    s = socket.create_connection((host, port), timeout=5)
    print("Socket connection successful!")
    s.close()
except Exception as e:
    print(f"Connectivity test failed: {e}")
    # We don't exit here to let alembic try anyway, but we've logged valuable info
EOF

# Run database migrations
echo "Running alembic migrations..."
alembic upgrade head

# Start background worker in the background
echo "Starting background worker..."
python -m app.workers.run_all &

# Start the web server
echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
