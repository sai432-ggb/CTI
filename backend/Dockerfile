FROM python:3.11-slim

# Install system dependencies (tshark for Wireshark integration)
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y tshark libpcap-dev gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]