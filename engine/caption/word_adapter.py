# FILE: engine/caption/word_adapter.py

def group_words_custom(words, config):
    """
    Hybrid Logic:
    Memotong kalimat jika:
    1. Jumlah kata >= max_words (Setting UI)
    2. ATAU Jeda antar kata >= min_silence (Default 0.5s)
    """
    max_words = config.get("max_words", 5)
    
    # Ambil silence threshold (default 0.5 detik jika tidak ada di config)
    min_silence_sec = config.get("min_silence", 0.5) 

    lines = []
    current_line = []
    
    for i, word in enumerate(words):
        # Tambahkan kata ke baris saat ini
        current_line.append(word)
        
        should_split = False
        
        # 1. Cek Jumlah Kata
        if len(current_line) >= max_words:
            should_split = True
            
        # 2. Cek Silence (Jeda) dengan kata berikutnya
        if not should_split and i < len(words) - 1:
            next_word = words[i+1]
            # Gap = Start kata depan - End kata sekarang
            gap = next_word['start'] - word['end']
            
            # Jika jeda lebih dari 0.5 detik (atau config), paksa ganti baris
            # Ini agar caption tidak menggantung saat orang diam lama
            if gap >= min_silence_sec:
                should_split = True

        # Eksekusi Split
        if should_split:
            lines.append(current_line)
            current_line = []
            
    # Sisa kata terakhir
    if current_line:
        lines.append(current_line)
        
    return lines

def format_lines_to_ass(grouped_lines):
    result = []
    for group in grouped_lines:
        if not group: continue
        
        start_time = group[0]['start']
        end_time = group[-1]['end']
        
        full_text = " ".join([w['text'] for w in group])
        
        result.append({
            "start": start_time,
            "end": end_time,
            "text": full_text,
            "words": group
        })
    return result