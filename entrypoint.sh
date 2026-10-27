#!/bin/sh
set -e

echo "=== Waiting for Database Connection ==="
python << 'EOF'
import os
import sys
import time
import psycopg2
from urllib.parse import urlparse

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not set, skipping wait.")
    sys.exit(0)

print(f"Connecting to database...")
connected = False
for attempt in range(1, 15):
    try:
        conn = psycopg2.connect(db_url)
        conn.close()
        print("Database connection successfully established!")
        connected = True
        break
    except Exception as e:
        print(f"Attempt {attempt}/15 failed: {e}. Retrying in 2 seconds...")
        time.sleep(2)

if not connected:
    print("Warning: Could not connect to database after 15 attempts. Proceeding with caution...")
EOF

echo "=== Applying Database Migrations ==="
python manage.py makemigrations admin_app website --noinput || true
python manage.py migrate --noinput

echo "=== Ensuring Admin Superuser ==="
python manage.py ensure_superuser

echo "=== Collecting Static Files ==="
python manage.py collectstatic --noinput || true

echo "=== Starting Server ==="
exec "$@"
