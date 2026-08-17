"""
image_preview.py — Widget hien thi anh (QLabel + QPixmap), dung
chung cho ca AliceView (anh goc) va BobView (anh sau giai ma).
"""
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class ImagePreview(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 240)
        self.setStyleSheet("border: 1px solid #888;")
        self.setText("Chua co anh")

    def set_image_from_path(self, path: str):
        pixmap = QPixmap(path)
        self.setPixmap(pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio))
