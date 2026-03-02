# 1. Use Python base
FROM python:3.11-slim

# 2. Set working directory inside the container
WORKDIR /app

# 3. Copy requirements using the path relative to the REPO ROOT
COPY shl-recommendation/backend/requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the ENTIRE repository (grabs backend and scripts)
COPY . .

# 6. Expose port
EXPOSE 8000

# 7. Start the app
# Note the path to app.py inside the subfolder
CMD ["uvicorn", "shl-recommendation.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]