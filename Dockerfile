# Build stage for React frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/renderer
COPY renderer/package*.json ./
RUN npm ci
COPY renderer/ ./
RUN npm run build

# Run stage for FastAPI backend
FROM python:3.10-slim

# Install system dependencies needed for PyMuPDF and others
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create user for Hugging Face Spaces
RUN useradd -m -u 1000 user

# Install Python dependencies (cloud version)
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt

# Copy backend code
COPY src/ ./src/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/renderer/dist ./renderer/dist

# Set environment variables for HF Spaces
ENV DEPLOYMENT_MODE=cloud
ENV HOST=0.0.0.0
ENV PORT=7860
# This creates a data directory inside the container for ephemeral storage
ENV DATA_DIR=/app/data

# Create necessary directories and set ownership for user 1000
RUN mkdir -p /app/data/uploads /app/data/chroma_db && \
    chown -R user:user /app

# Switch to the non-root user required by HF Spaces
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Expose port required by HF Spaces
EXPOSE 7860

# Run the FastAPI server
CMD sh -c "python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-7860}"
