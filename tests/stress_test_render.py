import sys
import os
import time

# ==============================================================================
# ⚠️ WAJIB DI ATAS: HACK PATH AGAR PYTHON MENEMUKAN FOLDER ROOT
# ==============================================================================
current_dir = os.path.dirname(os.path.abspath(__file__)) # Folder 'tests'
root_dir = os.path.dirname(current_dir)                  # Folder 'MAMENPRO_GUI' (Root)
sys.path.insert(0, root_dir)                             # Masukkan root ke sys.path paling depan

# ==============================================================================
# BARU BOLEH IMPORT MODUL PROJECT DI BAWAH SINI
# ==============================================================================
from PySide6.QtGui import QGuiApplication 
from manager.timeline.timeline_engine import TimelineEngine
from manager.timeline.layer_model import LayerModel
from manager.timeline.time_range import TimeRange
from manager.services.render_service import RenderWorker

def run_stress_test():
    # Inisialisasi Aplikasi GUI (Wajib untuk Font & QPainter)
    app = QGuiApplication(sys.argv) 
    
    print("🔥 STARTING STRESS TEST 🔥")
    print(f"Running from: {root_dir}")
    print("------------------------------------------------")
    
    # 1. Setup Timeline
    timeline = TimelineEngine()
    
    # Generate 100 Layer Teks
    layer_count = 100
    print(f"Generating {layer_count} overlapping text layers...")
    
    for i in range(layer_count):
        start = (i % 20) * 0.5 
        duration = 3.0
        
        layer = LayerModel(
            id=f"stress_{i}",
            type="text",
            time=TimeRange(start, start + duration),
            z_index=i,
            payload={
                "text_content": f"LAYER {i}",
                "x": (i * 15) % 1200,
                "y": (i * 15) % 600,
                "font_family": "Arial",
                "font_size": 40 + (i % 20),
                "text_color": "#ffffff" if i % 2 == 0 else "#ffcc00",
                "is_bold": True,
                "opacity": 0.9,
                "scale": 100,
                "rotation": (i * 10) % 360
            }
        )
        timeline.add_layer(layer)

    total_dur = timeline.get_total_duration()
    print(f"Timeline Duration: {total_dur:.2f}s")
    
    # 2. Config Render
    output_file = os.path.join(root_dir, "lililili.mp4")
    config = {
        "path": output_file,
        "width": 1280, 
        "height": 720,
        "fps": 30
    }
    
    print(f"Target Output: {output_file}")
    
    # 3. Jalankan Worker
    # Pastikan file render_service.py sudah diperbaiki dengan import QImage!
    worker = RenderWorker(timeline, config["path"], config)
    
    def on_progress(val):
        sys.stdout.write(f"\r🚀 Rendering: {val}% ")
        sys.stdout.flush()
        
    def on_finished(success, msg):
        print(f"\n\n------------------------------------------------")
        if success:
            print(f"✅ SUCCESS! Render finished.")
            print(f"📁 File saved to: {msg}")
        else:
            print(f"❌ FAILED! Error details below:")
            print(msg)
        worker.wait()   # ⬅️ TUNGGU THREAD BENAR-BENAR SELESAI
        app.quit()
        
    worker.sig_progress.connect(on_progress)
    worker.sig_finished.connect(on_finished)
    # Mute log internal agar tampilan terminal rapi
    worker.sig_log.connect(lambda m: None) 
    
    start_time = time.time()
    worker.start()
    
    # Blok terminal sampai selesai
    app.exec()
    
    elapsed = time.time() - start_time
    print(f"⏱️ Total Execution Time: {elapsed:.2f}s")

if __name__ == "__main__":
    run_stress_test()