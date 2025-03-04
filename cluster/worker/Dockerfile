FROM python:3.11-slim

WORKDIR /app

COPY pkg /opt/nc_pkg
COPY sec_data/worker /opt/worker_keychain

RUN for dir in /opt/nc_pkg/*/; do [ -d "$dir" ] && pip install --find-links=/opt/nc_pkg -e "$dir"; done

CMD ["python", "-m", "ndn_compute_worker"]
