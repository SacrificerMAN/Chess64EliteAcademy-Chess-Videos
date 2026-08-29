"""Make Telegram bot resilient: reels/shorts optional; safer ffmpeg writes."""
from pathlib import Path

agent = Path("chess_video_agent_v2.py")
if agent.exists():
    t = agent.read_text()
    old = 'clip.write_videofile(output_path, fps=FPS, codec="libx264", audio_codec="aac", logger=None)'
    new = (
        'clip.write_videofile(output_path, fps=FPS, codec="libx264", audio_codec="aac", '
        'logger=None, threads=1, preset="ultrafast", ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"])'
    )
    if old in t and 'preset="ultrafast"' not in t:
        t = t.replace(old, new)
        agent.write_text(t)
        print("agent write_videofile hardened")
    else:
        print("agent already hardened or pattern missing")

bot = Path("chess_telegram_bot_v2.py")
if bot.exists():
    t = bot.read_text()
    needle = 'await status.edit_text(f"⏳ {white} vs {black}\\n[3/5] Shorts + Reels…")'
    if needle in t and "reels optional" not in t:
        start = t.find(needle)
        end = t.find('await status.edit_text(f"⏳ {white} vs {black}\\n[4/5] Thumbnails + SEO…")', start)
        if start > 0 and end > start:
            wrapped = '''await status.edit_text(f"⏳ {white} vs {black}\\n[3/5] Shorts + Reels…")
        # reels optional — do not fail whole job on MoviePy/ffmpeg pipe errors
        try:
            shorts_path = job_dir / "shorts.mp4"
            await asyncio.to_thread(
                create_shorts_clip,
                analysis,
                str(shorts_path),
                move_duration=min(2.5, settings["duration"]),
                theme=settings["theme"],
                white_name=white,
                black_name=black,
                white_photo=wp,
                black_photo=bp,
                white_flag=wf,
                black_flag=bf,
            )
        except Exception as e:
            print(f"shorts failed (optional): {e}")
        try:
            reels_path = job_dir / "reels.mp4"
            await asyncio.to_thread(
                export_reels_vertical,
                analysis,
                str(reels_path),
                move_duration=min(2.2, settings["duration"]),
                theme=settings["theme"],
                white_name=white,
                black_name=black,
                white_photo=wp,
                black_photo=bp,
                white_flag=wf,
                black_flag=bf,
                clock_text=os.environ.get("CHESS_CLOCK", "10+0"),
            )
        except Exception as e:
            print(f"reels failed (optional): {e}")

        '''
            t = t[:start] + wrapped + t[end:]
            bot.write_text(t)
            print("bot shorts/reels made optional")
        else:
            print("bot block markers not found")
    else:
        print("bot already patched or needle missing")
print("done")
