# Passport Leader IDs for Testing

## Available Leaders (from seed data):

1. **Sheena** (Track Owner)
   - Leader ID: `524ccac3-1407-4bae-9e9a-4a3e580b9f7b`
   - Role: `track_owner`
   - Email: `sheena@example.com`

2. **Tom** (Mentor)
   - Leader ID: `66262e75-c95f-4598-a2bb-dad1177db9d6`
   - Role: `mentor`
   - Email: `tom@example.com`

3. **Emma** (Mentor)
   - Leader ID: `41a0bf63-2dac-4cc8-ae83-6b11ed778820`
   - Role: `mentor`
   - Email: `emma@example.com`

4. **Shannon** (Campus Pastor)
   - Leader ID: `87cbce39-4cc5-4880-9583-34a1034af934`
   - Role: `campus_pastor`
   - Email: `shannon@example.com`

5. **Mike** (Mentor)
   - Leader ID: `af9236fe-37e7-41bf-a45b-bf322fc61a89`
   - Role: `mentor`
   - Email: `mike@example.com`

6. **Lisa** (Mentor)
   - Leader ID: `13c9f3c4-de40-4653-a4b1-d30f55595f74`
   - Role: `mentor`
   - Email: `lisa@example.com`

## How to Login:

### Option 1: Use Existing Futures Pulse Login
Since Passport is integrated into Futures Pulse, just:
1. Login to Futures Pulse normally (your existing username/password)
2. Click "Passport" in the sidebar
3. The Passport page will use your existing session

### Option 2: Test Passport API Directly
If you want to test the Passport API endpoints directly:

```bash
curl -X POST http://localhost:8000/api/auth/dev-login \
  -H "Content-Type: application/json" \
  -d '{
    "leader_id": "524ccac3-1407-4bae-9e9a-4a3e580b9f7b",
    "email": "sheena@example.com",
    "role": "track_owner"
  }'
```

This returns a JWT token you can use for API calls.

### Option 3: Quick Test Login
Use any of the Leader IDs above with:
- Leader ID: Copy one from above
- Email: Any email (e.g., `test@test.com`)
- Role: `mentor`, `track_owner`, `campus_pastor`, or `admin`













