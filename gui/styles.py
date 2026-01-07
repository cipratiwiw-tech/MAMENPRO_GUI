import os

# Fungsi untuk memuat file .qss
def load_stylesheet():
    # Mendapatkan lokasi folder tempat file ini berada (gui/)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "styles.qss")
    
    try:
        with open(file_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: File tema tidak ditemukan di {file_path}")
        return ""

# Variabel ini nanti dipanggil di main.py
STYLESHEET = load_stylesheet()