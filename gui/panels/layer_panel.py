# gui/panels/layer_panel.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, 
                             QPushButton, QHBoxLayout, QListWidgetItem, QLabel, QAbstractItemView)
from PySide6.QtCore import Signal, Qt

class LayerPanel(QWidget):
    # OUTPUT SIGNALS
    sig_layer_selected = Signal(str)
    sig_request_add = Signal(str)
    sig_request_delete = Signal()
    # [BARU] Signal Reorder: (start_index, destination_index)
    sig_request_reorder = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #23272e; color: #dcdcdc;")
        self._id_map = {} 
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel("LAYERS")
        lbl_title.setStyleSheet("font-weight: bold; color: #56b6c2;")
        layout.addWidget(lbl_title)

        # List Widget Setup
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { border: 1px solid #3e4451; }
            QListWidget::item:selected { background-color: #3e4451; border-left: 2px solid #61afef; }
        """)
        
        # [BARU] AKTIFKAN DRAG & DROP
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Connect Signals
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        
        # [BARU] Tangkap event pindah baris
        self.list_widget.model().rowsMoved.connect(self._on_rows_moved)

        layout.addWidget(self.list_widget)

        # Buttons (Sama seperti sebelumnya)
        btn_layout = QHBoxLayout()
        self.btn_add_text = QPushButton("+ Text")
        self.btn_add_text.clicked.connect(lambda: self.sig_request_add.emit("text"))
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setStyleSheet("background-color: #e06c75; color: white;")
        self.btn_delete.clicked.connect(lambda: self.sig_request_delete.emit())
        
        btn_layout.addWidget(self.btn_add_text)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

    def _on_item_clicked(self, item):
        layer_id = item.data(Qt.UserRole)
        self.sig_layer_selected.emit(layer_id)

    def _on_rows_moved(self, parent, start, end, destination, row):
        """
        Logic internal Qt untuk drag-drop sedikit unik.
        Kita perlu menerjemahkan 'Qt Model Index' menjadi 'Simple List Index'.
        """
        # Simplifikasi: start adalah index awal, row adalah index tujuan
        # Karena di QListWidget 'end' biasanya sama dengan 'start' (pindah 1 item)
        
        # Koreksi index tujuan jika item dipindah ke bawah
        final_dest = row
        if row > start:
            final_dest = row - 1
            
        # Emit signal ke Controller
        self.sig_request_reorder.emit(start, final_dest)

    # --- API VISUAL ---
    def add_item_visual(self, layer_id: str, name: str):
        # Insert di row 0 (paling atas tumpukan UI = paling atas Z-Index)
        # TAPI: Dalam list visual, biasanya item atas = Z-index tinggi.
        # ProjectState kita: index 0 = Z-index 0 (paling bawah).
        # Jadi UI List harus DIBALIK urutannya atau logic add-nya disesuaikan.
        
        # Untuk SEMENTARA: Kita anggap List Index 0 = Background (Bawah).
        # Jadi add_item taruh di paling bawah list.
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, layer_id)
        self.list_widget.addItem(item) # Add to bottom
        self._id_map[layer_id] = item

    def remove_item_visual(self, layer_id: str):
        if layer_id in self._id_map:
            item = self._id_map[layer_id]
            self.list_widget.takeItem(self.list_widget.row(item))
            del self._id_map[layer_id]

    def select_item_visual(self, layer_id: str):
        if layer_id in self._id_map:
            item = self._id_map[layer_id]
            self.list_widget.setCurrentItem(item)
        else:
            self.list_widget.clearSelection()
            
    # [BARU] Fitur Block Signal saat refresh total
    def clear_visual(self):
        self.list_widget.clear()
        self._id_map.clear()