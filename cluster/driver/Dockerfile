FROM python:3.11-slim

WORKDIR /app

COPY pkg /opt/nc_pkg

RUN for dir in /opt/nc_pkg/*/; do [ -d "$dir" ] && pip install -e "$dir"; done

CMD ["python", "-m", "ndn_compute_rpc_server"]
