#!/bin/bash

echo "=== Starting Futures Link ==="
echo "Working directory: $(pwd)"
echo "Listing files:"
ls -la backend/ | head -20

echo ""
echo "Checking critical files:"
[ -f "backend/app.py" ] && echo "✓ app.py exists" || echo "✗ app.py MISSING"
[ -f "backend/users.json" ] && echo "✓ users.json exists" || echo "✗ users.json MISSING"
[ -f "backend/campuses.json" ] && echo "✓ campuses.json exists" || echo "✗ campuses.json MISSING"

echo ""
echo "Environment variables:"
echo "PORT=$PORT"
echo "PYTHONUNBUFFERED=$PYTHONUNBUFFERED"

echo ""
echo "=== Starting Python app ==="
cd backend
exec python -u app.py

