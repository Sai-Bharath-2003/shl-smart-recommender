FROM python:3.11-slim

# Install requirements first (cached layer)
COPY shl-recommendation/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy entire repo into /app
COPY . /app

# Debug: print the full directory tree so we can see exact paths in Render logs
RUN echo "=== CATALOG SEARCH ===" && find /app -name "shl_catalog.json" 2>/dev/null && echo "=== APP.PY LOCATION ===" && find /app -name "app.py" 2>/dev/null && echo "=== END ==="

# Set workdir to wherever app.py is — based on your repo: shl-recommendation/backend/
WORKDIR /app/shl-recommendation/backend

# Set catalog path explicitly
ENV CATALOG_PATH=/app/shl-recommendation/scripts/data/shl_catalog.json

# Verify at build time
RUN echo "Workdir contents:" && ls -la && echo "Catalog exists:" && test -f $CATALOG_PATH && echo "YES" || echo "NO — check CATALOG SEARCH output above"

CMD uvicorn app:app --host 0.0.0.0 --port $PORT