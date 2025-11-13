#!/bin/bash
echo "🧪 Testing Passport Integration"
echo ""

echo "1. Testing Passport API health endpoint:"
curl -s http://localhost:5002/api/passport/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:5002/api/passport/health
echo ""
echo ""

echo "2. Testing Passport API info endpoint (requires login):"
curl -s http://localhost:5002/api/passport/info | python3 -m json.tool 2>/dev/null || curl -s http://localhost:5002/api/passport/info
echo ""
echo ""

echo "3. Testing session endpoint:"
curl -s http://localhost:5002/api/session | python3 -m json.tool 2>/dev/null || curl -s http://localhost:5002/api/session
echo ""
echo ""

echo "✅ If you see JSON responses, the API is working!"
echo "⚠️  If you see 404s, restart your backend server"
