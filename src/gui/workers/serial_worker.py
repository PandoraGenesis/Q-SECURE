"""
serial_worker.py — Doc/ghi du lieu voi ESP32 qua SerialManager tren
mot QThread rieng, tranh block giao dien khi cho phan hoi phan cung.
"""
from PyQt6.QtCore import QThread, pyqtSignal


class SerialWorker(QThread):
    line_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)

    def __init__(self, serial_manager, parent=None):
        super().__init__(parent)
        self.serial_manager = serial_manager
        self._running = False

    def run(self):
        self._running = True
        self.serial_manager.open()
        while self._running:
            line = self.serial_manager.read_line()
            if line:
                self.line_received.emit(line)

    def stop(self):
        self._running = False
        self.serial_manager.close()
