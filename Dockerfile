# SafeShip Orders API — Day 2 (app only; PostgreSQL added on Day 3)
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY app ./app

# Run as a non-root user for least-privilege container execution.
RUN useradd --create-home --shell /bin/bash safeship && \
    chown -R safeship:safeship /app
USER safeship

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
