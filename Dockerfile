FROM python:3.12-slim

# ffmpeg (render), stockfish (analysis), and cairo/pango libs (cairosvg
# rendering of the chess board SVG) — all required at runtime, not just build.
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

ENV PORT=8080 \
    CHESS64_WORKDIR=/tmp/chess64_jobs \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 8080

CMD ["bash", "scripts/start.sh"]
