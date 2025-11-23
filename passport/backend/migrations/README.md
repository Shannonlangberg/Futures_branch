# Alembic Migrations

This directory contains database migrations for the Futures Pulse Passport application.

## Usage

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

## Environment

Make sure `DATABASE_URL` is set in your environment before running migrations.












