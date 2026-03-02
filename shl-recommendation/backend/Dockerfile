FROM python:3.11-slim

WORKDIR /app

# 1. Copy requirements from the full repo path
COPY shl-recommendation/backend/requirements.txt .

# 2. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy EVERYTHING into the container (this grabs scripts/ and backend/)
COPY . .

EXPOSE 8000

# 4. Run uvicorn (assuming app.py is inside the backend folder)
CMD ["uvicorn", "shl-recommendation.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]