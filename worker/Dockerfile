FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

# Inject safety flags to force pip to tolerate slower or unstable network connections
RUN pip install --no-cache-dir --default-timeout=1000 --retries 5 -r requirements.txt

COPY . .

CMD ["python", "src/worker.py"]
