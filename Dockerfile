FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY server.py .
COPY firefly_client.py .

RUN pip install --no-cache-dir "mcp[cli]>=1.6.0" "httpx>=0.27.0"

ENV FIREFLY_URL=http://localhost:8080/api/v1
ENV FIREFLY_IMPORTER_URL=http://localhost:8081

CMD ["python", "server.py"]
