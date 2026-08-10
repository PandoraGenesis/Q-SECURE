"""
alice_view.py — Giao dien danh cho may gui (Alice): chon anh goc,
nut bat dau sinh khoa/sifting, log qua trinh, nut gui du lieu.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

from src.gui.widgets.image_preview import ImagePreview
from src.gui.widgets.log_console import LogConsole


class AliceView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Q-SECURE - Alice (May gui)"))
        layout.addWidget(ImagePreview())

        self.btn_start = QPushButton("Bat dau QKD + Gui anh")
        layout.addWidget(self.btn_start)

        self.log_console = LogConsole()
        layout.addWidget(self.log_console)

        # TODO: ket noi self.btn_start.clicked toi NetworkWorker/SerialWorker
