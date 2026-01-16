import os

def ass_time(seconds):
    """
    Mengubah detik (float) menjadi format waktu ASS (H:MM:SS.cc).
    Menggunakan integer math untuk menghindari error format float.
    """
    if seconds is None:
        seconds = 0.0
    
    # Pastikan input adalah float sebelum dikali
    seconds = float(seconds)
    
    # Konversi total waktu ke centiseconds (1/100 detik) dan bulatkan jadi integer
    total_cs = int(round(seconds * 100))
    
    # Hitung Jam
    h = total_cs // 360000
    rem = total_cs % 360000
    
    # Hitung Menit
    m = rem // 6000
    rem = rem % 6000
    
    # Hitung Detik
    s = rem // 100
    
    # Hitung Centiseconds (sisa)
    cs = rem % 100
    
    # Return string format ASS (H:MM:SS.cc)
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
    margin_v=50
):
    # Header minimalis untuk fungsi legacy ini
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

# --- Updated build_ass_file function ---

def build_ass_file(subtitles, config=None):
    """
    Membuat file .ass berdasarkan subtitles dan config visual dari UI.
    """
    # Default Config jika kosong
    if config is None:
        config = {
            "font": "Arial", "font_size": 42, "text_color": "#ffffff",
            "stroke_color": "#000000", "stroke_width": 2
        }

    # Konversi Warna Hex #RRGGBB ke format ASS &HBBGGRR&
    def hex_to_ass_color(hex_str):
        if not hex_str or len(hex_str) < 7: return "&H00FFFFFF"
        r = hex_str[1:3]; g = hex_str[3:5]; b = hex_str[5:7]
        return f"&H00{b}{g}{r}"

    primary_color = hex_to_ass_color(config.get("text_color"))
    outline_color = hex_to_ass_color(config.get("stroke_color"))
    font_name = config.get("font", "Arial")
    font_size = config.get("font_size", 42)
    border_width = config.get("stroke_width", 2)
    
    # ... Header ASS ...
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},&H000000FF,{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1, {border_width},0,2,10,10,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # ... Loop Events ...
    events = ""
    for sub in subtitles:
        start = ass_time(sub["start"])
        end = ass_time(sub["end"])
        text = sub["text"]
        events += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n"

    filename = os.path.join(os.getcwd(), "temp_caption.ass")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(header + events)
        
    return filename