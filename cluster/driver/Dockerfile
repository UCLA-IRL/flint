FROM python:3.12-slim

WORKDIR /app

# Copy requirements.txt and install dependencies
COPY cluster/driver/requirements.txt .
COPY pkg/ndn_compute /opt
RUN pip install --no-cache-dir -r requirements.txt


CMD ["python", "driver.py"]
