"""
In-memory job store. A "job" is one render request from one Telegram user.

Railway's single-instance polling deployment means an in-memory dict is fine;
if you ever run multiple web replicas, swap this for Redis (keep the same
interface so nothing else needs to change).
"""
from __future__ import annotations

import os
import shutil
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from app.config import settings


@dataclass
class Job:
    id: str
    user_id: int
    status: str = "queued"  # queued|photos|rendering_long|rendering_shorts|seo|ready|error
    step: int = 0
    total_steps: int = 5
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    data: dict[str, Any] = field(default_factory=dict)  # game, meta, paths, overrides

    @property
    def workdir(self) -> str:
        path = os.path.join(settings.workdir, self.id)
        os.makedirs(path, exist_ok=True)
        return path

    def set_step(self, step: int, status: str) -> None:
        self.step = step
        self.status = status

    STATUS_LABELS = {
        1: "[1/5] Photos",
        2: "[2/5] Rendering long",
        3: "[3/5] Shorts",
        4: "[4/5] Thumbnails + SEO",
        5: "[5/5] Ready",
    }

    @property
    def status_label(self) -> str:
        return self.STATUS_LABELS.get(self.step, self.status)


_JOBS: dict[str, Job] = {}
# per-user sticky state for multi-message flows like /pgn, /setwhite, /setwhiteflag
_USER_STATE: dict[int, dict[str, Any]] = {}


def new_job(user_id: int) -> Job:
    job = Job(id=uuid.uuid4().hex[:12], user_id=user_id)
    _JOBS[job.id] = job
    return job


def get_job(job_id: str) -> Optional[Job]:
    return _JOBS.get(job_id)


def latest_job_for_user(user_id: int) -> Optional[Job]:
    user_jobs = [j for j in _JOBS.values() if j.user_id == user_id]
    return max(user_jobs, default=None, key=lambda j: j.created_at)


def cleanup_job(job_id: str) -> None:
    job = _JOBS.pop(job_id, None)
    if job:
        shutil.rmtree(job.workdir, ignore_errors=True)


def user_state(user_id: int) -> dict[str, Any]:
    return _USER_STATE.setdefault(
        user_id,
        {
            "awaiting": None,  # e.g. "pgn" | "photo_white" | "photo_black"
            "duration": settings.default_duration_per_move,
            "depth": settings.default_depth,
            "theme": settings.board_theme,
            "manual_photos": {},  # {"white": path, "black": path}
            "manual_flags": {},  # {"white": "IR", "black": "US"}
        },
    )


def clear_manual_assets(user_id: int) -> None:
    st = user_state(user_id)
    st["manual_photos"] = {}
    st["manual_flags"] = {}
