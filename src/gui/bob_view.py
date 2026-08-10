"""
bob_view.py — Giao dien danh cho may nhan (Bob): hien thi anh sau
giai ma, hien thi QBER, log qua trinh nhan du lieu.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

from src.gui.widgets.image_preview import ImagePreview
from src.gui.widgets.log_console import LogConsole


class BobView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Q-SECURE - Bob (May nhan)"))

        self.qber_label = QLabel("QBER: --")
        layout.addWidget(self.qber_label)

        self.image_preview = ImagePreview()
        layout.addWidget(self.image_preview)

        self.log_console = LogConsole()
        layout.addWidget(self.log_console)

        # TODO: khoi dong NetworkWorker (TcpServer) ngay khi view duoc tao
