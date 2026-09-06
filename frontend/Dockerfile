# Base Python image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set container working directory
WORKDIR /app

# Install system curl for health checks (optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose default Streamlit port
EXPOSE 8501

# Run Streamlit server bound to 0.0.0.0
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
