# Futures Pulse Passport

A discipleship and leadership tracking platform for Futures Church. Track discipleship progression like a passport, assign mentors, and award digital stamps.

## Features

- **Push → Mentor → Stamp Workflow**: Assign people to mentors, track progress, and award stamps
- **AI-Powered Push Queue**: Smart heuristics to identify people ready to move forward
- **Leader Dashboard**: View inbox, capacity, and assignments
- **User Passport**: See stamps earned, current zone, and next steps
- **Reports**: Track health and mentor load

## Tech Stack

- **Backend**: Python 3.11 + Flask + SQLModel + Alembic
- **Database**: SQLite (dev) → Postgres (prod)
- **Frontend**: Next.js 14 (App Router) + TypeScript + TailwindCSS
- **Auth**: JWT with dev mode header support

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- pip and npm/pnpm

### Backend Setup

```bash
cd passport/backend
pip install -r requirements.txt

# Set up environment
cp ../../.env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Seed database
python -m services.seed

# Run server
python app.py
```

Backend will run on `http://localhost:8000`

### Frontend Setup

```bash
cd passport/web
npm install
# or
pnpm install

# Set up environment
cp ../.env.example .env.local
# Edit .env.local with your settings

# Run dev server
npm run dev
# or
pnpm dev
```

Frontend will run on `http://localhost:3000`

## Docker Compose

```bash
cd passport/infra
docker-compose up
```

This will start:
- API on port 8000
- Web on port 3000
- Postgres on port 5432

## Usage

### Dev Login

1. Go to `http://localhost:3000/login`
2. Enter a leader ID (from seed data, e.g., a leader UUID)
3. Click "Login (Dev Mode)"

### Acceptance Criteria

1. ✅ Leader logs in (dev), sees Inbox with assignments
2. ✅ Push person → Sheena → transfer created
3. ✅ Sheena accepts → completes → stamp auto-awarded
4. ✅ Person sees new stamp + next step on `/passport/me`
5. ✅ Reports show mentor load & track funnel
6. ✅ Swap DATABASE_URL to Postgres → works unchanged

## API Endpoints

- `POST /api/auth/dev-login` - Dev mode login
- `GET /api/leaders/me` - Current leader profile
- `GET /api/people` - List people
- `GET /api/inbox` - Leader's assignments
- `GET /api/push-queue` - Candidates ready to move
- `POST /api/push` - Create assignment + transfer
- `POST /api/transfer/{id}/accept` - Accept transfer
- `POST /api/complete` - Mark assignment complete
- `GET /api/stamps/pending` - Pending stamps
- `GET /api/tracks` - List tracks
- `GET /api/reports/track-health` - Track health metrics
- `GET /api/reports/mentor-load` - Mentor capacity
- `GET /api/passport/{person_id}` - User passport view

## Seed Data

The seed script creates:
- Campus: Copper Coast
- Track: Worship (4 stops: Join Team, Rehearsals, Workshop, Platform Shadowing)
- 6 Leaders (Sheena, Tom, Emma, Shannon, Mike, Lisa)
- 12 People (8 assigned to track)
- 5 Assignments (first stop)

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Environment Variables

See `.env.example` for all available options.

Key variables:
- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - JWT secret key
- `DEV_AUTH_ENABLED` - Enable dev mode auth
- `CORS_ORIGINS` - Allowed CORS origins

## Project Structure

```
passport/
├── backend/
│   ├── app.py              # Flask app
│   ├── core/               # Core modules (db, auth)
│   ├── models/             # SQLModel models
│   ├── routes/             # API route blueprints
│   ├── services/           # Business logic
│   └── migrations/         # Alembic migrations
├── web/
│   ├── app/                # Next.js App Router pages
│   ├── components/         # React components
│   └── lib/                # Utilities (API client)
└── infra/
    └── docker-compose.yml  # Docker setup
```

## Development

### Backend

```bash
cd passport/backend
python app.py
```

### Frontend

```bash
cd passport/web
npm run dev
```

## Production Deployment

1. Set `DATABASE_URL` to Postgres connection string
2. Set `SECRET_KEY` to secure random value
3. Set `DEV_AUTH_ENABLED=false`
4. Build frontend: `npm run build`
5. Run migrations: `alembic upgrade head`
6. Seed data: `python -m services.seed`

## License

Private - Futures Church











