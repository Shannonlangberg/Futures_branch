# Multi-stage build for Futures Link

# Stage 1: Build Frontend
FROM node:18 AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend
FROM python:3.10-slim
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/dist ./backend/static

# Create necessary directories
RUN mkdir -p backend/instance backend/logs backend/uploads backend/temp_audio backend/exports backend/data

# Set environment variable for Railway
ENV PORT=5002
ENV PYTHONUNBUFFERED=1

# Expose port (Railway will override PORT env var)
EXPOSE ${PORT}

# Start the application
CMD ["python", "-u", "backend/app.py"]

