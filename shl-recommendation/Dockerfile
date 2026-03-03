# 1. Use Python base
FROM python:3.11-slim

# 2. Set working directory inside the container
WORKDIR /app

# 3. Copy requirements from the correct nested path
# We use the path relative to the REPO ROOT
COPY shl-recommendation/backend/requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the ENTIRE repository
COPY . .

# 6. Expose port
EXPOSE 8000

# 7. Start the app
# Corrected path to the FastAPI app object in app.py
# Replace your current Step 7 with this:
# This moves into the folder where your code lives, then starts uvicorn
CMD ["sh", "-c", "cd shl-recommendation/backend && uvicorn app:app --host 0.0.0.0 --port 10000"]

