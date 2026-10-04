FROM python:3.11-slim

# Set environment flags
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    PLAYWRIGHT_HEADLESS=true

WORKDIR /app

# Install system build dependencies and utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser and OS dependencies
RUN playwright install --with-deps chromium

# Copy source trees
COPY backend/ /app/backend/
COPY mock-finance-app/ /app/mock-finance-app/

WORKDIR /app/backend

# Pre-generate simulated enterprise invoices
RUN python data/seed_data/generate_invoices.py

# Expose port (Render sets $PORT dynamically)
EXPOSE 8000

# Run FastAPI via Uvicorn
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
