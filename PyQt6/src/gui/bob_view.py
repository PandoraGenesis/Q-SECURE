"""
bob_view.py — Giao dien danh cho may nhan (Bob): hien thi anh sau
giai ma, hien thi QBER, log qua trinh nhan du lieu.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

from src.gui.widgets.image_preview import ImagePreview
from src.gui.widgets.log_console import LogConsole
from src.gui.widgets.semaphore_indicator import SemaphoreIndicator


class BobView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Hermex - Bob (May nhan)"))

        self.qber_label = QLabel("QBER: --")
        layout.addWidget(self.qber_label)

        # Hien thi truc quan goc ma Bob "do" duoc (basis Bob dang dung
        # de doc LDR) - cap nhat bang self.semaphore_indicator.set_angle(angle)
        # moi khi nhan duoc du lieu goc tu SerialWorker/NetworkWorker.
        self.semaphore_indicator = SemaphoreIndicator()
        layout.addWidget(self.semaphore_indicator)

        self.image_preview = ImagePreview()
        layout.addWidget(self.image_preview)

        self.log_console = LogConsole()
        layout.addWidget(self.log_console)

        # TODO: khoi dong NetworkWorker (TcpServer) ngay khi view duoc tao
