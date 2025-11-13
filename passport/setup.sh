#!/bin/bash

# Futures Pulse Passport Setup Script

set -e

echo "🚀 Setting up Futures Pulse Passport..."

# Backend setup
echo "📦 Setting up backend..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

# Copy .env if it doesn't exist
if [ ! -f ".env" ]; then
    cp ../.env.example .env
    echo "✅ Created .env file (edit it with your settings)"
fi

# Run migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Seed database
echo "🌱 Seeding database..."
python -m services.seed

echo "✅ Backend setup complete!"
deactivate
cd ..

# Frontend setup
echo "📦 Setting up frontend..."
cd web
npm install

# Copy .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    cp ../.env.example .env.local
    echo "✅ Created .env.local file (edit it with your settings)"
fi

echo "✅ Frontend setup complete!"
cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "To start the frontend:"
echo "  cd web"
echo "  npm run dev"
echo ""





