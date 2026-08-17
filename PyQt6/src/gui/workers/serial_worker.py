"""
serial_worker.py — Cau noi giua SerialManager (src/hardware/esp32_serial.py)
va giao dien PyQt6, chay tren mot QThread rieng.

SerialManager tu quan ly luong doc nen rieng (threading.Thread thuan,
khong phu thuoc PyQt6) va mot hang doi thread-safe (queue.Queue). Lop
SerialWorker o day chi lam nhiem vu "cau noi": lap lay du lieu tu
SerialManager.get_latest_reading() va PHAT lai duoi dang tin hieu Qt
(pyqtSignal) de widget GUI nhan va cap nhat an toan giua cac luong.

Lenh GUI CHU DONG gui xuong ESP32 (vd nut bam goi send_servo_angle())
KHONG can di qua worker nay - co the goi truc tiep tu luong chinh vi
do la thao tac ghi nhanh, khong chan lau.
"""
from PyQt6.QtCore import QThread, pyqtSignal

from src.hardware.esp32_serial import SerialConnectionError, SerialNotConnectedError


class SerialWorker(QThread):
    reading_received = pyqtSignal(object)  # phat 1 SensorReading moi nhan duoc
    connected = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, serial_manager, parent=None):
        super().__init__(parent)
        self.serial_manager = serial_manager
        self._running = False

    def run(self):
        self._running = True

        try:
            self.serial_manager.connect()
            self.serial_manager.start_listening()
            self.connected.emit()
        except SerialConnectionError as e:
            self.error_occurred.emit(str(e))
            return

        while self._running:
            try:
                # timeout=0.5: block toi da 0.5s tren CHINH luong nay (khong
                # phai luong GUI), nen hoan toan an toan - day cung la chu ky
                # de vong lap kiem tra co lenh dung (_running) hay chua.
                reading = self.serial_manager.get_latest_reading(timeout=0.5)
                if reading is not None:
                    self.reading_received.emit(reading)
            except SerialNotConnectedError as e:
                self.error_occurred.emit(str(e))
                break

    def stop(self):
        self._running = False
        self.serial_manager.disconnect()
        self.wait()
