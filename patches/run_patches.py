"""
Applies every patch_XX_*.py in this directory, in numeric order, exactly
once per container start. Mirrors the documented conceptual deploy order:

  Player resolve fixes -> brand logo -> pro studio look -> broadcast elite ->
  16:9 pad -> ffmpeg frame normalize -> speed defaults -> Gemini viral+model ->
  pro channel footer -> bot manual photos/flags/help/syntax/stability -> start

Each patch module exposes a single `apply() -> None` function and must be
idempotent (safe to run every deploy, even though nothing here is stateful
across deploys in this scaffold — that's what makes "run every start" safe).
"""
from __future__ import annotations

import glob
import importlib.util
import logging
import os
import sys

logger = logging.getLogger("chess64.patches")
logging.basicConfig(level=logging.INFO)

PATCH_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PATCH_DIR)

# Running as `python patches/run_patches.py` only puts patches/ on sys.path,
# not the project root — so `from app...` imports inside each patch would
# fail with ModuleNotFoundError. Make sure the root is importable regardless
# of how this script is invoked (direct, -m, or from a different cwd).
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _load_module(path: str):
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def main() -> None:
    patch_files = sorted(glob.glob(os.path.join(PATCH_DIR, "patch_*.py")))
    if not patch_files:
        logger.info("No patches found.")
        return
    for path in patch_files:
        name = os.path.basename(path)
        try:
            module = _load_module(path)
            if hasattr(module, "apply"):
                module.apply()
                logger.info("✅ applied %s", name)
            else:
                logger.warning("⚠️ %s has no apply(); skipped", name)
        except Exception as exc:
            # Non-fatal: one bad patch must not kill web + Telegram on Railway.
            logger.error("❌ %s failed: %s (continuing)", name, exc)


if __name__ == "__main__":
    main()
