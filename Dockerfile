FROM python:3.12-slim

ARG BUILD_ID=famous-traps-v2-voice-20260930
ENV CHESS64_BUILD_ID=${BUILD_ID}

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        stockfish \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x scripts/start.sh
RUN python assets/audio/decode_sounds.py || true

ENV PORT=8080 \
    CHESS64_WORKDIR=/tmp/chess64_jobs \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/usr/games:${PATH}"

EXPOSE 8080

CMD ["bash", "scripts/start.sh"]
