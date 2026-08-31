"""Professional studio look + stronger YouTube SEO templates for Chess64."""
from pathlib import Path

agent = Path("chess_video_agent_v2.py")
if not agent.exists():
    print("no agent")
    raise SystemExit(0)

t = agent.read_text()
n = 0

old_canvas = 'canvas = Image.new("RGBA", (total_w, total_h), (28, 28, 28, 255))'
new_canvas = 'canvas = Image.new("RGBA", (total_w, total_h), (12, 16, 28, 255))  # pro studio navy'
if old_canvas in t:
    t = t.replace(old_canvas, new_canvas)
    n += 1
    print("canvas -> studio navy")

old_bar = 'draw.rectangle([0, y0, total_w, y0 + label_h], fill=(36, 36, 36, 255))'
new_bar = 'draw.rectangle([0, y0, total_w, y0 + label_h], fill=(18, 24, 40, 255))'
if old_bar in t:
    t = t.replace(old_bar, new_bar)
    n += 1
    print("player bars darker")

old_eval_bg = 'expanded = Image.new("RGBA", (new_w, total_h), (28, 28, 28, 255))'
new_eval_bg = 'expanded = Image.new("RGBA", (new_w, total_h), (12, 16, 28, 255))'
if old_eval_bg in t:
    t = t.replace(old_eval_bg, new_eval_bg)
    n += 1

t2 = t.replace('apply_brand_logo(out, corner="br"', 'apply_brand_logo(out, corner="tl"')
t2 = t2.replace('apply_brand_logo(img.convert("RGB"), corner="br"', 'apply_brand_logo(img.convert("RGB"), corner="tl"')
if t2 != t:
    t = t2
    n += 1
    print("logo -> top-left")

if 'DEFAULT_THEME = "green"' in t:
    t = t.replace('DEFAULT_THEME = "green"', 'DEFAULT_THEME = "brown"', 1)
    n += 1
    print("default theme brown")

old_desc = '''    desc_en += [
        "",
        "Watch the key ideas, tactics, and the decisive moment.",
        "Silent board + arrows style for clean study / shorts.",
        "",
        "👍 Like | 💬 Comment | 🔔 Subscribe for daily chess",
    ]
    desc_hi += [
        "",
        "जरूरी आइडिया, टैक्टिक्स और फैसलाकुन पल देखें।",
        "साइलेंट बोर्ड + एरो स्टाइल — पढ़ाई और शॉर्ट्स के लिए।",
        "",
        "👍 लाइक | 💬 कमेंट | 🔔 रोज़ाना शतरंज के लिए सब्सक्राइब",
    ]'''

new_desc = '''    desc_en += [
        "",
        "Watch the key ideas, tactics, and the decisive moment.",
        "Professional board analysis by Chess64 Elite Academy.",
        "",
        "📌 Subscribe for daily GM games, traps & Hindi/English coaching.",
        "📱 Telegram: https://t.me/Messi9354",
        "",
        "👍 Like | 💬 Comment | 🔔 Turn on notifications",
        "",
        "#Chess64EliteAcademy",
    ]
    desc_hi += [
        "",
        "जरूरी आइडिया, टैक्टिक्स और फैसलाकुन पल देखें।",
        "Chess64 Elite Academy — प्रोफेशनल बोर्ड एनालिसिस।",
        "",
        "📌 रोज़ाना GM गेम्स, ट्रैप्स और Hindi/English कोचिंग के लिए सब्सक्राइब करें।",
        "📱 टेलीग्राम: https://t.me/Messi9354",
        "",
        "👍 लाइक | 💬 कमेंट | 🔔 नोटिफिकेशन ऑन करें",
        "",
        "#Chess64EliteAcademy",
    ]'''

if old_desc in t:
    t = t.replace(old_desc, new_desc)
    n += 1
    print("description CTA branded")

old_tags = '''    tags_core = [
        "chess", "chessgame", "chessmaster", "grandmaster",
        "chessmoves", "chessplay", "chessshorts", "chessvideo",
        "stockfish", "tactics", "checkmate", "chesshighlights",
        "shatranj", "shatranjgame", "chesshindi",
    ]'''
new_tags = '''    tags_core = [
        "chess", "chess64", "chess64eliteacademy", "grandmaster",
        "chessanalysis", "chessgame", "chessmaster", "chessmoves",
        "chessshorts", "chesshighlights", "tactics", "checkmate",
        "stockfish", "otbchess", "chesshindi", "shatranj",
        "chessopening", "chessstrategy", "fide", "lichess",
    ]'''
if old_tags in t:
    t = t.replace(old_tags, new_tags)
    n += 1
    print("hashtags improved")

needle = "    # ---- English titles ----\n    titles_en = []\n"
inject = '''    # ---- English titles ----
    titles_en = []
    if event and event.lower() not in ("live chess", "chess.com", "?"):
        titles_en.append(f"{w_last} vs {b_last} | {event}"[:100])
        if hook and hook not in ("INSANE GAME",):
            titles_en.append(f"{hook}: {w_last} vs {b_last} | {event}"[:100])
'''
if needle in t and "if event and event.lower()" not in t:
    t = t.replace(needle, inject, 1)
    n += 1
    print("event-aware titles")

old_paste = "    canvas.paste(board_img, (0, label_h))\n    draw = ImageDraw.Draw(canvas)"
new_paste = '''    canvas.paste(board_img, (0, label_h))
    draw = ImageDraw.Draw(canvas)
    # thin gold studio frame around board
    try:
        x0, y0b = 0, label_h
        x1, y1b = total_w - 1, label_h + board_img.height - 1
        draw.rectangle([x0, y0b, x1, y1b], outline=(201, 162, 39, 180), width=2)
    except Exception:
        pass'''
if old_paste in t and "gold studio frame" not in t:
    t = t.replace(old_paste, new_paste, 1)
    n += 1
    print("gold board frame")

agent.write_text(t)
print(f"patch_pro_studio: {n} changes")
