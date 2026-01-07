import os
from datetime import datetime

# ============================================================
# BUNDLER FINAL – ENGINE MAMENPRO (WHITELIST + BLACKLIST)
# ============================================================

OUTPUT_FILENAME = "MAMENPRO_app2.txt"

# -----------------------------
# WHITELIST (ROOT LEVEL)
# -----------------------------
ENGINE_FOLDERS = {
    # "analysis",
    "assets",
    # "audio_pipeline",
    "caption",
    "effects",
    "engine",
    "gui",
    "utils",
    "manager"
    # 
}

# -----------------------------
# BLACKLIST FOLDER (GLOBAL)
# (berlaku di mana pun)
# -----------------------------
BLACKLIST_FOLDERS = {
    "__pycache__",
    ".venv",
    "tests",
    "test",
    "experimental",
    "deprecated",
    "backup",
    "draft",
}

# -----------------------------
# BLACKLIST FILE (BY NAME)
# -----------------------------
BLACKLIST_FILES = {
    "__init__old.py",
    "debug.py",
    "scratch.py",
    "bundler.py",
    "extractor.py",
    # "main_window.py",
    "project.json",
    # "main.py",
    "MENSPRO.py"
}

# -----------------------------
# EXTENSION YANG DIIZINKAN
# -----------------------------
ALLOWED_EXTENSIONS = (
    ".py",
    ".json",
    ".ttf",
    ".otf",
)

# File eksplisit
EXTRA_FILES = {
    # "requirements.txt",
    "main.py",
}

# ============================================================

def is_allowed_file(filename: str) -> bool:
    if filename in BLACKLIST_FILES:
        return False
    return (
        filename.endswith(ALLOWED_EXTENSIONS)
        or filename in EXTRA_FILES
    )

def is_blacklisted_path(path: str) -> bool:
    parts = path.split(os.sep)
    return any(p in BLACKLIST_FOLDERS for p in parts)

def bundle_engine():
    root_path = os.getcwd()
    bundled_count = 0

    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as outfile:
        # HEADER
        outfile.write("=" * 90 + "\n")
        outfile.write("MAMENPRO ENGINE BUNDLE\n")
        outfile.write(f"ROOT PATH : {root_path}\n")
        outfile.write(f"CREATED   : {datetime.now()}\n")
        outfile.write("MODE      : WHITELIST + BLACKLIST\n")
        outfile.write("CONTENT   : ENGINE ONLY\n")
        outfile.write("=" * 90 + "\n\n")

        for root, dirs, files in os.walk(root_path):
            rel_root = os.path.relpath(root, root_path)

            # -----------------------------
            # ROOT LEVEL → WHITELIST
            # -----------------------------
            if rel_root == ".":
                dirs[:] = [d for d in dirs if d in ENGINE_FOLDERS]
                continue

            # -----------------------------
            # CEK TOP-LEVEL ENGINE
            # -----------------------------
            top_folder = rel_root.split(os.sep)[0]
            if top_folder not in ENGINE_FOLDERS:
                dirs[:] = []
                continue

            # -----------------------------
            # BLACKLIST FOLDER FILTER
            # -----------------------------
            dirs[:] = [
                d for d in dirs
                if d not in BLACKLIST_FOLDERS
            ]

            # -----------------------------
            # FILE LOOP
            # -----------------------------
            for file in files:
                if not is_allowed_file(file):
                    continue

                if file == os.path.basename(__file__) or file == OUTPUT_FILENAME:
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_path)

                if is_blacklisted_path(rel_path):
                    continue

                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    outfile.write("\n" + "=" * 90 + "\n")
                    outfile.write(f"FILE: {rel_path}\n")
                    outfile.write("=" * 90 + "\n")
                    outfile.write(content + "\n")

                    bundled_count += 1
                    print(f"[OK] {rel_path}")

                except Exception as e:
                    print(f"[SKIP] {rel_path} -> {e}")

        outfile.write("\n" + "=" * 90 + "\n")
        outfile.write(f"TOTAL FILES BUNDLED: {bundled_count}\n")
        outfile.write("=" * 90 + "\n")

    print("\n✅ ENGINE BUNDLE SELESAI")
    print(f"📦 OUTPUT: {OUTPUT_FILENAME}")
    print(f"📁 FILES : {bundled_count}")

# ============================================================

if __name__ == "__main__":
    bundle_engine()
