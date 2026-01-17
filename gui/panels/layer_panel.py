# gui/panels/layer_panel.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, 
                             QPushButton, QHBoxLayout, QListWidgetItem, QLabel)
from PySide6.QtCore import Signal, Qt

class LayerPanel(QWidget):
    # Sinyal OUTPUT (Hanya berteriak, tidak memerintah)
    sig_layer_selected = Signal(str)      # Mengirim Layer ID
    sig_request_add = Signal(str)         # Mengirim Tipe Layer ('text', 'shape')
    sig_request_delete = Signal()         # Request hapus layer aktif
    sig_request_reorder = Signal(int, int)# Request pindah urutan (opsional)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        
        # Mapping internal untuk menghubungkan QListWidgetItem <-> Layer ID
        # Ini murni untuk keperluan visual UI, bukan logic bisnis
        self._id_map = {} 

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        lbl_title = QLabel("LAYERS")
        lbl_title.setStyleSheet("font-weight: bold; color: #56b6c2;")
        layout.addWidget(lbl_title)

        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("border: 1px solid #3e4451;")
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        # Buttons Container
        btn_layout = QHBoxLayout()
        
        self.btn_add_text = QPushButton("+ Text")
        self.btn_add_text.clicked.connect(lambda: self.sig_request_add.emit("text"))
        
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setStyleSheet("background-color: #e06c75; color: white;")
        self.btn_delete.clicked.connect(lambda: self.sig_request_delete.emit())

        btn_layout.addWidget(self.btn_add_text)
        btn_layout.addWidget(self.btn_delete)
        
        layout.addLayout(btn_layout)

    # --- INPUT DARI USER (INTERNAL UI) ---
    def _on_item_clicked(self, item):
        # Cari ID dari item yang diklik
        layer_id = item.data(Qt.UserRole)
        self.sig_layer_selected.emit(layer_id)

    # --- PERINTAH DARI BINDER (EKSTERNAL) ---
    # Panel ini 'bodoh', dia hanya melakukan apa yang disuruh Binder

    def add_item_visual(self, layer_id: str, name: str):
        """Menambah item ke list visual"""
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, layer_id) # Simpan ID di metadata item UI
        self.list_widget.insertItem(0, item) # Insert di atas (stack order)
        self._id_map[layer_id] = item

    def remove_item_visual(self, layer_id: str):
        """Menghapus item dari list visual"""
        if layer_id in self._id_map:
            item = self._id_map[layer_id]
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
            del self._id_map[layer_id]

    def select_item_visual(self, layer_id: str):
        """Highlight item tertentu"""
        if layer_id in self._id_map:
            item = self._id_map[layer_id]
            self.list_widget.setCurrentItem(item)
        else:
            self.list_widget.clearSelection()