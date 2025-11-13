#!/bin/bash
echo "🧪 Quick Passport Test"
echo ""
echo "1. Backend API Health:"
curl -s http://localhost:5002/api/passport/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:5002/api/passport/health
echo ""
echo ""
echo "2. Can you see 'Passport' in the sidebar at http://localhost:5002/dashboard?"
echo "   - If YES: ✅ Working!"
echo "   - If NO: Frontend needs rebuild"
echo ""
echo "3. Try going directly to: http://localhost:5002/passport"
