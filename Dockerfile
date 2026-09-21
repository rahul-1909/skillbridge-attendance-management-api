FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY submission/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY submission/ /app/submission/
COPY main.py /app/main.py

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV AUTO_SEED=true

EXPOSE 8000

CMD ["sh", "-c", "uvicorn submission.src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
