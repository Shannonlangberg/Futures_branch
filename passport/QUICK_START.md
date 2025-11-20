# Quick Start Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- pip and npm/pnpm

## One-Command Setup

```bash
cd passport
./setup.sh
```

## Manual Setup

### Backend

```bash
cd passport/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../.env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Seed database
python -m services.seed

# Start server
python app.py
```

Backend runs on `http://localhost:8000`

### Frontend

```bash
cd passport/web

# Install dependencies
npm install
# or
pnpm install

# Set up environment
cp ../.env.example .env.local
# Edit .env.local with your settings

# Start dev server
npm run dev
# or
pnpm dev
```

Frontend runs on `http://localhost:3000`

## First Login

1. Go to `http://localhost:3000/login`
2. For dev login, you need a leader ID from the seed data
3. Check the seed script or database to get a leader ID
4. Or use the first leader ID from the seed output

## Test the Flow

1. **Login** as a leader (e.g., Tom - mentor)
2. **View Inbox** - see assignments
3. **Push Queue** - see candidates ready to move
4. **Push** a person to a mentor
5. **Accept** transfer (as the mentor)
6. **Complete** assignment - stamp auto-awarded
7. **View Passport** - see stamps earned

## Docker

```bash
cd passport/infra
docker-compose up
```

## Troubleshooting

### Database errors
- Make sure migrations are run: `alembic upgrade head`
- Check DATABASE_URL in .env

### Import errors
- Make sure you're in the virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

### CORS errors
- Check CORS_ORIGINS in backend .env
- Make sure frontend URL matches

### Frontend not connecting
- Check NEXT_PUBLIC_API_URL in web/.env.local
- Make sure backend is running on port 8000










