def normalize_words(words):
    """
    Normalize AssemblyAI word list
    (data sudah dalam DETIK)
    """

    out = []

    for w in words:
        text = (
            w.get("text")
            or w.get("word")
            or w.get("punctuated_word")
        )

        if not text:
            continue

        out.append({
            "word": text.upper(),
            "start": float(w["start"]),
            "end": float(w["end"])
        })

    return out
