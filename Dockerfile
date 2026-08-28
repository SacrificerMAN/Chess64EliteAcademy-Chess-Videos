FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    fonts-dejavu-core \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sL "https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-ubuntu-x86-64.tar" \
    -o /tmp/sf.tar \
    && tar xf /tmp/sf.tar -C /tmp \
    && cp /tmp/stockfish/stockfish-ubuntu-x86-64 /usr/local/bin/stockfish \
    && chmod +x /usr/local/bin/stockfish \
    && rm -rf /tmp/sf.tar /tmp/stockfish

WORKDIR /app

# Copy everything from repo
COPY . .

# If only zip was uploaded, extract full source over /app
RUN if [ -f chess64_final_bundle.zip ]; then \
      unzip -o chess64_final_bundle.zip -d /app && \
      rm -f chess64_final_bundle.zip; \
    fi

# Prefer requirements from extracted tree
RUN if [ -f requirements_chess_agent_v2.txt ]; then \
      pip install --no-cache-dir -r requirements_chess_agent_v2.txt; \
    else \
      pip install --no-cache-dir fastapi uvicorn[standard] python-multipart chess cairosvg moviepy pillow edge-tts numpy; \
    fi

ENV STOCKFISH_PATH=/usr/local/bin/stockfish
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080
CMD ["uvicorn", "webapp.app:app", "--host", "0.0.0.0", "--port", "8080"]
