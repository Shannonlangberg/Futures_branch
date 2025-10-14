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

# Expose port (Railway will set PORT env var)
EXPOSE 5002

# Start the application
CMD ["python", "backend/app.py"]

