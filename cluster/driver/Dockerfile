FROM python:3.11-slim

WORKDIR /app

COPY pkg /opt/nc_pkg
COPY sec_data/driver /opt/driver_keychain
# I guess this is needed? really feels like a hack
COPY generated_data/distributed/fs-manifest.json .

RUN for dir in /opt/nc_pkg/*/; do [ -d "$dir" ] && pip install --find-links=/opt/nc_pkg -e "$dir"; done

CMD ["python", "-m", "ndn_compute_driver"]
