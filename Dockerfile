# Dockerfile for Railway deployment
# Use a lightweight Python base image
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire repository into the container
COPY . .

# Expose the port Railway will assign (default $PORT)
EXPOSE 8000

# Run the FastAPI app from the backend folder
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
