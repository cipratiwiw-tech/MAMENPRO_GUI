import sys
import os
import time

# Hack Path (Wajib paling atas)
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.insert(0, root_dir)

from PySide6.QtGui import QGuiApplication 
from manager.timeline.timeline_engine import TimelineEngine
from manager.timeline.layer_model import LayerModel
from manager.timeline.time_range import TimeRange
from manager.services.render_service import RenderWorker

# ======================================================
# 👇 GANTI INI DENGAN PATH VIDEO ASLI DI KOMPUTER ANDA!
# Contoh Windows: r"C:\Users\rtauf\Videos\contoh.mp4"
# ======================================================
VIDEO_SOURCE_PATH = r"C:\Users\rtauf\Desktop\BotBuatanMamen\MAMENPRO_GUI\contoh.mp4" 

def run_audio_test():
    app = QGuiApplication(sys.argv)
    
    print("🔊 STARTING AUDIO RENDER TEST 🔊")
    
    # Validasi File
    if "Path" in VIDEO_SOURCE_PATH or not os.path.exists(VIDEO_SOURCE_PATH):
        print("❌ ERROR: Anda belum mengganti VIDEO_SOURCE_PATH di script ini!")
        print("   Silakan edit file tests/test_audio_render.py baris 20.")
        return

    # 1. Setup Timeline
    timeline = TimelineEngine()
    
    # Buat 1 Layer Video (Durasi 5 detik)
    print(f"Adding Video Source: {os.path.basename(VIDEO_SOURCE_PATH)}")
    
    layer = LayerModel(
        id="video_test_01",
        type="video", # <--- TIPE HARUS VIDEO AGAR SUARA DIAMBIL
        time=TimeRange(0.0, 5.0), # Ambil 5 detik pertama
        z_index=0,
        payload={
            "path": VIDEO_SOURCE_PATH,
            "start_time": 0.0, # Offset di timeline (0 detik)
            "x": 0, "y": 0, "scale": 100, "opacity": 1.0, "rotation": 0
        }
    )
    timeline.add_layer(layer)
    
    # 2. Config Output
    output_file = os.path.join(root_dir, "test_audio_output.mp4")
    config = {
        "path": output_file,
        "width": 1280, 
        "height": 720,
        "fps": 30
    }
    
    # 3. Run Worker
    worker = RenderWorker(timeline, config["path"], config)
    
    def on_progress(val):
        sys.stdout.write(f"\r🚀 Rendering: {val}% ")
        sys.stdout.flush()
        
    def on_finished(success, msg):
        print("\n------------------------------------------------")
        if success:
            print(f"✅ SUCCESS! Cek file: {msg}")
        else:
            print(f"❌ FAILED! {msg}")
        app.quit()
        
    worker.sig_progress.connect(on_progress)
    worker.sig_finished.connect(on_finished)
    # Tampilkan log internal untuk debugging audio command
    worker.sig_log.connect(print) 
    
    worker.start()
    app.exec()

if __name__ == "__main__":
    run_audio_test()