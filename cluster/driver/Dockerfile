FROM python:3.12-slim

WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../../pkg/ndn_compute /opt/ndn_compute
RUN ls /opt/ndn_compute
RUN pip install -e /opt/ndn_compute

CMD ["python", "driver.py"]
