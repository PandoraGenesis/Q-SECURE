"""
serial_worker.py
=================
SerialWorker(QThread) - luong PyQt6 doc lap, chay ben duoi giao dien
chinh, lien tuc doc gia tri LDR tu ESP32 qua cong Serial USB va phat
tin hieu ve GUI ma khong lam dong bang (Not Responding) giao dien.

Tai su dung SerialManager tu esp32_serial.py (da xay dung va kiem thu
rieng o mot buoc truoc do trong du an) de xu ly phan ket noi/doc du
lieu/xu ly ngoai le tang thap - file nay chi dong vai tro "cau noi":
lay du lieu tu hang doi thread-safe cua SerialManager (chay bang
threading.Thread thuan, khong phu thuoc PyQt6) roi phat lai duoi dang
tin hieu Qt (pyqtSignal), de widget GUI cap nhat an toan giua cac luong.
"""
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from esp32_serial import SerialConnectionError, SerialManager

# Neu khong nhan duoc dong du lieu LDR nao trong qua lau (giay), coi
# nhu ket noi da chet (rut cap USB, ESP32 treo...) - vi firmware du an
# gui LDR rat deu dan (dinh ky hoac ngay sau moi lenh goc), im lang qua
# lau la dau hieu bat thuong ro rang, khong phai do doi lenh binh thuong.
DEFAULT_SILENCE_TIMEOUT_S = 5.0


class SerialWorker(QThread):
    """
    Chay tren 1 QThread rieng, doc lien tuc gia tri LDR tu ESP32 qua
    Serial USB. Phat data_received(int) moi khi co gia tri LDR moi.
    Phat error_occurred(str) neu khong ket noi duoc tu dau, hoac phat
    hien mat ket noi giua chung (rut cap USB dot ngot, cong bien mat...).
    """

    data_received = pyqtSignal(int)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        silence_timeout_s: float = DEFAULT_SILENCE_TIMEOUT_S,
        parent=None,
    ):
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self.silence_timeout_s = silence_timeout_s
        self._manager: Optional[SerialManager] = None
        self._running = False

    def run(self):
        self._running = True
        self._manager = SerialManager(port=self.port, baudrate=self.baudrate)

        try:
            self._manager.connect()
            self._manager.start_listening()
        except SerialConnectionError as e:
            self.error_occurred.emit(f"Không kết nối được ESP32: {e}")
            return

        seconds_since_last_data = 0.0
        poll_interval_s = 0.5  # cung la chu ky vong lap kiem tra co lenh dung (_running) hay chua

        # Vong lap vo han: get_latest_reading(timeout=...) block toi da
        # poll_interval_s giay roi tra ve None neu chua co gi moi - day
        # KHONG phai vong lap ban (busy loop) chiem CPU vo ich, ma la
        # nhip kiem tra dinh ky vua de nhan du lieu vua de phat hien
        # mat ket noi va kiem tra co lenh dung tu GUI hay chua.
        while self._running:
            reading = self._manager.get_latest_reading(timeout=poll_interval_s)

            if reading is not None:
                seconds_since_last_data = 0.0
                self.data_received.emit(reading.ldr_value)
                continue

            seconds_since_last_data += poll_interval_s

            # Kiem tra ca hai dau hieu: ket noi da bao dong (is_connected
            # tra ve False) HOAC im lang qua lau bat thuong - cong voi
            # nhau de khong bo sot truong hop nao, vi ban than
            # is_open cua pyserial khong phai luc nao cung cap nhat
            # ngay lap tuc khi thiet bi vat ly bien mat.
            if not self._manager.is_connected():
                self.error_occurred.emit("Mất kết nối USB với ESP32 (cổng đã đóng hoặc cáp bị rút).")
                break

            if seconds_since_last_data >= self.silence_timeout_s:
                self.error_occurred.emit(
                    f"Không nhận được dữ liệu LDR nào trong {self.silence_timeout_s:.0f}s — "
                    f"nghi ngờ cáp USB bị rút hoặc ESP32 bị treo."
                )
                break

        if self._manager.is_connected():
            self._manager.disconnect()

    def stop(self):
        """Goi TU LUONG CHINH (GUI) de dung luong doc mot cach an toan."""
        self._running = False
        self.wait(2000)
