FROM python:3.11-slim

WORKDIR /app

# Copy requirements.txt and install dependencies
COPY cluster/driver/requirements.txt .
COPY pkg/ndn_compute /opt/ndn_compute

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e /opt/ndn_compute


CMD ["python", "driver.py"]
