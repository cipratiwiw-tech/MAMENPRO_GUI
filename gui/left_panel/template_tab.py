import os
import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QInputDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal

# Folder penyimpanan
TEMPLATE_DIR = "saved_templates"

class TemplateTab(QScrollArea):
    # Sinyal saat user klik "Load" pada salah satu template
    sig_load_template = Signal(dict) 

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setStyleSheet("border: none;") 
        
        # Pastikan folder ada
        if not os.path.exists(TEMPLATE_DIR):
            os.makedirs(TEMPLATE_DIR)
            
        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        
        # Header / Refresh Button
        header = QFrame()
        h_layout = QVBoxLayout(header)
        btn_refresh = QPushButton("🔄 Refresh List")
        btn_refresh.clicked.connect(self.refresh_grid)
        h_layout.addWidget(btn_refresh)
        self.main_layout.addWidget(header)
        
        # Grid Container
        self.grid_container = QWidget()
        self.grid = QGridLayout(self.grid_container)
        self.grid.setSpacing(15)
        self.main_layout.addWidget(self.grid_container)
        
        self.main_layout.addStretch()
        self.setWidget(container)
        
        # Load awal
        self.refresh_grid()

    def refresh_grid(self):
        """ Membaca folder JSON dan membuat kartu grid """
        # Hapus widget lama
        for i in reversed(range(self.grid.count())): 
            self.grid.itemAt(i).widget().setParent(None)
            
        files = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith(".json")]
        
        for idx, filename in enumerate(files):
            name = filename.replace(".json", "")
            self._add_template_card(idx, name, filename)

    def _add_template_card(self, index, name, filename):
        card = QFrame()
        card.setFixedSize(140, 170)
        card.setStyleSheet("""
            QFrame { background-color: #3c3836; border: 1px solid #504945; border-radius: 8px; }
            QFrame:hover { border: 1px solid #fe8019; }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 1. Preview (Placeholder Warna)
        thumb = QLabel("TEMPLATE")
        thumb.setStyleSheet("background-color: #458588; color: white; border-radius: 4px; font-weight: bold;")
        thumb.setFixedSize(128, 90)
        thumb.setAlignment(Qt.AlignCenter)
        
        # 2. Nama
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet("color: #ebdbb2; font-weight: bold; border: none; background: transparent;")
        lbl_name.setAlignment(Qt.AlignCenter)
        
        # 3. Tombol Load
        btn_load = QPushButton("Load")
        btn_load.setCursor(Qt.PointingHandCursor)
        btn_load.setStyleSheet("background-color: #d65d0e; color: white; border: none; border-radius: 3px;")
        btn_load.clicked.connect(lambda: self.load_from_file(filename))

        # 4. Tombol Delete (Kecil)
        btn_del = QPushButton("Del")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet("background-color: #282828; color: #cc241d; border: 1px solid #cc241d; border-radius: 3px;")
        btn_del.clicked.connect(lambda: self.delete_file(filename))
        
        layout.addWidget(thumb)
        layout.addWidget(lbl_name)
        layout.addWidget(btn_load)
        layout.addWidget(btn_del)
        
        row = index // 2
        col = index % 2
        self.grid.addWidget(card, row, col)

    def save_new_template(self, data_dict):
        """ Dipanggil oleh Main.py saat user klik Save di PreviewPanel """
        name, ok = QInputDialog.getText(self, "Save Template", "Masukkan Nama Template:")
        if ok and name:
            filepath = os.path.join(TEMPLATE_DIR, f"{name}.json")
            try:
                with open(filepath, 'w') as f:
                    json.dump(data_dict, f, indent=4)
                QMessageBox.information(self, "Success", f"Template '{name}' berhasil disimpan!")
                self.refresh_grid()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal menyimpan: {str(e)}")

    def load_from_file(self, filename):
        filepath = os.path.join(TEMPLATE_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.sig_load_template.emit(data) # Kirim data ke Main -> Preview
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat: {str(e)}")

    def delete_file(self, filename):
        filepath = os.path.join(TEMPLATE_DIR, filename)
        confirm = QMessageBox.question(self, "Hapus", f"Hapus template '{filename}'?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            os.remove(filepath)
            self.refresh_grid()