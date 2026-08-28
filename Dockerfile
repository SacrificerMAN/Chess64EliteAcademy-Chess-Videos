FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    shared-mime-info fonts-dejavu-core curl unzip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sL "https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-ubuntu-x86-64.tar" \
    -o /tmp/sf.tar \
    && tar xf /tmp/sf.tar -C /tmp \
    && cp /tmp/stockfish/stockfish-ubuntu-x86-64 /usr/local/bin/stockfish \
    && chmod +x /usr/local/bin/stockfish \
    && rm -rf /tmp/sf.tar /tmp/stockfish

WORKDIR /app
COPY . .

RUN if [ -f chess64_final_bundle.zip ]; then \
      unzip -o chess64_final_bundle.zip -d /tmp/bundle && \
      for f in chess_video_agent_v2.py chess_telegram_bot_v2.py youtube_uploader.py watch_folder.py \
               chess_agent_config.json requirements_chess_agent_v2.txt \
               chess_move_self.mp3 chess_capture.mp3 chess_move_check.mp3; do \
        if [ -f /tmp/bundle/$f ]; then cp -f /tmp/bundle/$f /app/$f; fi; \
      done && \
      if [ -d /tmp/bundle/traps ]; then cp -rf /tmp/bundle/traps /app/; fi && \
      rm -f chess64_final_bundle.zip; \
    fi

RUN if [ -f webapp/_parts/assemble.sh ]; then sh webapp/_parts/assemble.sh; fi
RUN touch webapp/__init__.py

RUN pip install --no-cache-dir -r requirements_chess_agent_v2.txt

ENV STOCKFISH_PATH=/usr/local/bin/stockfish
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
EXPOSE 8080
CMD ["uvicorn", "webapp.app:app", "--host", "0.0.0.0", "--port", "8080"]
