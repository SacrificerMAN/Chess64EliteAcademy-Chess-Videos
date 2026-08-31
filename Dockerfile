FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    shared-mime-info fonts-dejavu-core curl unzip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-ubuntu-x86-64.tar" -o /tmp/sf.tar \
 && tar xf /tmp/sf.tar -C /tmp \
 && cp /tmp/stockfish/stockfish-ubuntu-x86-64 /usr/local/bin/stockfish \
 && chmod +x /usr/local/bin/stockfish \
 && rm -rf /tmp/sf.tar /tmp/stockfish \
 && stockfish quit || true

WORKDIR /app
COPY . .

RUN if [ -f chess64_final_bundle.zip ]; then \
      unzip -qo chess64_final_bundle.zip -d /tmp/bundle && \
      for f in chess_video_agent_v2.py youtube_uploader.py \
               watch_folder.py chess_agent_config.json requirements_chess_agent_v2.txt \
               chess_move_self.mp3 chess_capture.mp3 chess_move_check.mp3; do \
        [ -f /tmp/bundle/$f ] && cp -f /tmp/bundle/$f /app/; \
      done && \
      if [ -f /tmp/bundle/chess_telegram_bot_v2.py ]; then \
        cp -f /tmp/bundle/chess_telegram_bot_v2.py /app/; \
      fi && \
      [ -d /tmp/bundle/traps ] && cp -rf /tmp/bundle/traps /app/; \
      rm -rf /tmp/bundle chess64_final_bundle.zip; \
    fi

RUN python3 install_fix_resolve.py || true
RUN python3 apply_player_fix.py || true
RUN python3 expand_known.py || true
RUN python3 patch_agent_bugs.py || true
RUN python3 patch_brand_logo.py || true
RUN python3 patch_pro_studio.py || true
RUN python3 patch_bot_stability.py || true
RUN python3 patch_bot_manual_photos.py || true
RUN sh webapp/_parts/assemble.sh || true
RUN touch webapp/__init__.py
RUN chmod +x wire_photo_fix.sh start.sh && sh wire_photo_fix.sh || true

RUN pip install --no-cache-dir -r requirements_chess_agent_v2.txt \
 && rm -rf /root/.cache/pip /tmp/*

ENV STOCKFISH_PATH=/usr/local/bin/stockfish
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "start.sh"]
