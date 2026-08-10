"""
log_console.py — O log dang doc (QPlainTextEdit) de hien thi tien
trinh sifting / QBER / trang thai ket noi cho nguoi dung theo doi.
"""
from PyQt6.QtWidgets import QPlainTextEdit


class LogConsole(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(1000)

    def append_log(self, message: str):
        self.appendPlainText(message)
