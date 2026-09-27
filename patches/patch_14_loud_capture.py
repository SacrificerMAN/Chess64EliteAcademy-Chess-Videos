"""Patch 14 — make capture sound loud and always distinct from move click."""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LOUD_SYNTH = r'''
def _build_synth_kind(
    timestamps_sec: list[float],
    total_duration_sec: float,
    out_path: str,
    kind: str = "capture",
) -> str:
    """Loud, distinct capture thud or bright check ping (phone-speaker friendly)."""
    delays_ms = [max(0, int(ts * 1000)) for ts in timestamps_sec]
    n = len(delays_ms)
    if not n:
        return build_move_click_track([], total_duration_sec, out_path, None)

    inputs: list[str] = []
    filter_parts: list[str] = []

    if kind == "check":
        for i, d in enumerate(delays_ms):
            inputs += ["-f", "lavfi", "-i", "sine=frequency=880:duration=0.06"]
            inputs += ["-f", "lavfi", "-i", "sine=frequency=1320:duration=0.05"]
            a, b = 2 * i, 2 * i + 1
            filter_parts.append(
                f"[{a}:a]volume=1.2,afade=t=out:st=0:d=0.06,adelay={d}|{d}[a{i}]"
            )
            filter_parts.append(
                f"[{b}:a]volume=0.9,afade=t=out:st=0:d=0.05,adelay={d+40}|{d+40}[b{i}]"
            )
        mix_inputs = "".join(f"[a{i}][b{i}]" for i in range(n))
        n_in = 2 * n
    else:
        # capture: deep thud + sharp noise slap
        for i, d in enumerate(delays_ms):
            inputs += ["-f", "lavfi", "-i", "sine=frequency=70:duration=0.12"]
            inputs += ["-f", "lavfi", "-i", "sine=frequency=140:duration=0.08"]
            inputs += ["-f", "lavfi", "-i", "anoisesrc=color=white:duration=0.06:sample_rate=44100"]
            a, b, c = 3 * i, 3 * i + 1, 3 * i + 2
            filter_parts.append(
                f"[{a}:a]volume=1.6,afade=t=out:st=0:d=0.12,adelay={d}|{d}[a{i}]"
            )
            filter_parts.append(
                f"[{b}:a]volume=1.2,afade=t=out:st=0:d=0.08,adelay={d}|{d}[b{i}]"
            )
            filter_parts.append(
                f"[{c}:a]highpass=f=1000,lowpass=f=8000,volume=1.1,"
                f"afade=t=out:st=0:d=0.05,adelay={d}|{d}[c{i}]"
            )
        mix_inputs = "".join(f"[a{i}][b{i}][c{i}]" for i in range(n))
        n_in = 3 * n

    filter_complex = ";".join(filter_parts) + (
        f";{mix_inputs}amix=inputs={n_in}:duration=longest:normalize=0,"
        f"alimiter=limit=0.98,apad=whole_dur={total_duration_sec}[mixed]"
    )
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[mixed]", "-t", str(total_duration_sec), "-c:a", "aac", out_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg {kind} synth failed: {proc.stderr[-1500:]}")
    return out_path


'''


def apply() -> None:
    p = ROOT / "app" / "render" / "video_builder.py"
    t = p.read_text()

    if "Always use distinct synth for capture" not in t:
        old_cap = '''    if by_kind["capture"]:
        part = f"{base}_capture.aac"
        if cap_p:
            build_move_click_track(by_kind["capture"], total_duration_sec, part, cap_p)
        else:
            _build_synth_kind(by_kind["capture"], total_duration_sec, part, kind="capture")
        partials.append(part)'''
        new_cap = '''    if by_kind["capture"]:
        part = f"{base}_capture.aac"
        # Always use distinct synth for capture (asset files were often corrupt/missing)
        _build_synth_kind(by_kind["capture"], total_duration_sec, part, kind="capture")
        partials.append(part)'''
        if old_cap in t:
            t = t.replace(old_cap, new_cap, 1)
            print("capture forced to synth")
        else:
            print("capture branch pattern not exact")

    if "frequency=70" in t and "volume=1.6" in t:
        print("loud synth already present")
        p.write_text(t)
        return

    if "def _build_synth_kind" in t:
        start = t.index("def _build_synth_kind")
        rest = t[start + 4 :]
        rel = rest.find("\ndef ")
        if rel < 0:
            print("could not find end of _build_synth_kind")
            p.write_text(t)
            return
        end = start + 4 + rel
        t = t[:start] + LOUD_SYNTH.lstrip("\n") + t[end:]
        p.write_text(t)
        print("upgraded to loud capture synth")
    else:
        print("_build_synth_kind missing — run patch_11 first")
        p.write_text(t)
