"""Patch 13 — never crash the job on bad narration / audio mix."""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def apply() -> None:
    vb = ROOT / "app" / "render" / "video_builder.py"
    t = vb.read_text()
    if "using primary track only" in t or "Fail-soft" in t:
        print("video_builder mix already soft")
    else:
        old = (
            "    proc = subprocess.run(cmd, capture_output=True, text=True)\n"
            "    if proc.returncode != 0:\n"
            "        raise RuntimeError(f\"FFmpeg audio mix failed: {proc.stderr[-1500:]}\")\n"
            "    return out_path\n"
        )
        new = (
            "    proc = subprocess.run(cmd, capture_output=True, text=True)\n"
            "    if proc.returncode != 0:\n"
            "        import shutil as _shutil\n"
            "        print(\"audio mix failed, using primary track only\")\n"
            "        _shutil.copy(tracks[0], out_path)\n"
            "        return out_path\n"
            "    return out_path\n"
        )
        if old in t:
            t = t.replace(old, new, 1)
            t = t.replace(
                "tracks = [t for t in track_paths if t]",
                "tracks = [p for p in track_paths if p and os.path.isfile(p) and os.path.getsize(p) >= 100]",
                1,
            )
            vb.write_text(t)
            print("patched mix soft-fail")
        else:
            print("mix pattern not found")

    pl = ROOT / "app" / "pipeline.py"
    pt = pl.read_text()
    if "audio mix skipped, clicks only" in pt:
        print("pipeline mix already soft")
        return
    old_m = (
        "    audio_path = click_track_path\n"
        "    if narration_path:\n"
        "        mixed_path = os.path.join(workdir, \"audio_mixed.aac\")\n"
        "        audio_path = mix_audio_tracks([click_track_path, narration_path], mixed_path)\n"
    )
    new_m = (
        "    audio_path = click_track_path\n"
        "    if narration_path:\n"
        "        try:\n"
        "            mixed_path = os.path.join(workdir, \"audio_mixed.aac\")\n"
        "            audio_path = mix_audio_tracks([click_track_path, narration_path], mixed_path)\n"
        "        except Exception as e:\n"
        "            logger.warning(\"audio mix skipped, clicks only: %s\", e)\n"
        "            audio_path = click_track_path\n"
    )
    if old_m in pt:
        pt = pt.replace(old_m, new_m, 1)
        pl.write_text(pt)
        print("patched pipeline mix soft")
    else:
        print("pipeline mix pattern not found")
