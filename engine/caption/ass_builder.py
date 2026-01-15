def ass_time(ms):
    total = ms // 1000
    cs = (ms // 10) % 100
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def chunk_words(words, n):
    buf = []
    for w in words:
        buf.append(w)
        if len(buf) == n:
            yield buf
            buf = []
    if buf:
        yield buf


def ass_color_from_hex(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
    return f"&H00{b}{g}{r}"


def make_ass_from_words(
    words,
    words_per_event=3, # Default chunk size
    font="Arial",
    size=40,
    color="&H00FFFFFF", # Ingat format ASS warnanya BBGGRR (terbalik dari RGB)
    outline=2,
    outline_color="&H00000000",
    align=2,   # 2 = bottom-center
    margin_v=120
):
    ...

    header = f"""
[Script Info]
ScriptType: v4.00+
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BorderStyle,Outline,Alignment
Style: Default,{font},{size},{color},{outline_color},1,{outline},2

[Events]
Format: Layer, Start, End, Style, Text
""".strip()

    events = []
    for group in chunk_words(words, words_per_event):
        start = ass_time(group[0]["start"])
        end = ass_time(group[-1]["end"])
        text = " ".join(w["text"] for w in group)
        events.append(f"Dialogue: 0,{start},{end},Default,{text}")

    return header + "\n" + "\n".join(events)
