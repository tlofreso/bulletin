FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Marker
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY models.py server.py ./

# Expose port
EXPOSE 8000

# Pre-download Marker models on build (optional, makes container larger but faster startup)
# RUN python -c "from marker.models import create_model_dict; create_model_dict()"

# Run server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
