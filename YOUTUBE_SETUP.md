# YouTube upload on Railway (Telegram bot)

Railway is headless — browser OAuth cannot run there. Do OAuth **once on your PC**, then upload tokens.

## 1. Google Cloud
1. https://console.cloud.google.com → new project
2. Enable **YouTube Data API v3**
3. OAuth consent screen → External → add your Gmail as test user
4. Credentials → **OAuth client ID** → Application type: **Desktop app**
5. Download JSON → rename to `client_secrets.json`

## 2. Authorize once (on your laptop)
```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
# put client_secrets.json next to youtube_uploader.py
python -c "from youtube_uploader import get_youtube_service; get_youtube_service()"
```
Browser opens → login → allow → creates `token.json`.

## 3. Put files on Railway (base64 env)
```bash
base64 -w0 client_secrets.json   # → CLIENT_SECRETS_B64
base64 -w0 token.json            # → YOUTUBE_TOKEN_B64
```
Add both as Railway Variables. `start.sh` writes them to `/app/` on boot.

## 4. Extra variables
```
YOUTUBE_CLIENT_SECRETS=/app/client_secrets.json
YOUTUBE_TOKEN=/app/token.json
YOUTUBE_PRIVACY=private
```
