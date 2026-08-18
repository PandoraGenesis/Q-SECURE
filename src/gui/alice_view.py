"""
alice_view.py — Giao dien danh cho may gui (Alice): chon anh goc,
nut bat dau sinh khoa/sifting, log qua trinh, nut gui du lieu.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

from src.gui.widgets.image_preview import ImagePreview
from src.gui.widgets.log_console import LogConsole
from src.gui.widgets.semaphore_indicator import SemaphoreIndicator


class AliceView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Hermex - Alice (May gui)"))
        layout.addWidget(ImagePreview())

        # Hien thi truc quan goc Servo/basis dang gui di - moi lan
        # SerialManager.send_servo_angle(angle) duoc goi, cap nhat
        # widget nay bang self.semaphore_indicator.set_angle(angle)
        # de nguoi xem thay ngay goc nao dang duoc truyen.
        self.semaphore_indicator = SemaphoreIndicator()
        layout.addWidget(self.semaphore_indicator)

        self.btn_start = QPushButton("Bat dau QKD + Gui anh")
        layout.addWidget(self.btn_start)

        self.log_console = LogConsole()
        layout.addWidget(self.log_console)

        # TODO: ket noi self.btn_start.clicked toi NetworkWorker/SerialWorker
        # Trong ham xu ly do, sau moi lan goi send_servo_angle(angle),
        # goi them: self.semaphore_indicator.set_angle(angle)
