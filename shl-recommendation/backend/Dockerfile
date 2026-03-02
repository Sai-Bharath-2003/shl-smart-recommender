# 1. Start from Python base
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /app

# 3. Copy requirements using the FULL path from the root
# Note: Since the context is the root, we must specify the subfolder
COPY shl-recommendation/backend/requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the ENTIRE project into the container
# This ensures 'scripts' and 'backend' are both available
COPY . .

# 6. Expose the port
EXPOSE 8000

# 7. Command to run (adjust path if main.py is in backend/)
CMD ["uvicorn", "shl-recommendation.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]