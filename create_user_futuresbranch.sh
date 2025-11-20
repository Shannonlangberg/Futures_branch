#!/bin/bash
# Create user via API on futuresbranch
curl -X POST https://futuresbranch-production.up.railway.app/api/users/create \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Shannon Langberg",
    "email": "shannon.langberg@futures.church",
    "password": "futures2025",
    "full_name": "Shannon Langberg",
    "role": "admin",
    "campus": "copper_coast"
  }'
