"""
FastAPI web process. On Railway this runs alongside the Telegram poller
(see scripts/start.sh) purely so Railway has an HTTP port to health-check —
the bot itself does the real work via polling, not webhooks, by default.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.config import settings
from app.storage import get_job

app = FastAPI(title="Chess64 Elite Academy")


@app.get("/")
def root():
    return {"service": "chess64-elite-academy", "status": "ok", "channel": settings.channel_name}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "status": job.status,
        "step": job.step,
        "label": job.status_label,
        "error": job.error,
        "ready": job.step == 5,
    }
