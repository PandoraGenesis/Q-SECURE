"""
esp32_serial.py — Lop SerialManager: mo/dong cong COM, doc/ghi
du lieu voi board ESP32 thong qua PySerial.
"""
import serial

from config import SERIAL_CONFIG


class SerialManager:
    def __init__(self, port: str = SERIAL_CONFIG["COM_PORT"], baudrate: int = SERIAL_CONFIG["BAUD_RATE"]):
        self.port = port
        self.baudrate = baudrate
        self._conn: serial.Serial | None = None

    def open(self):
        self._conn = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=SERIAL_CONFIG["SERIAL_TIMEOUT"],
        )

    def write_command(self, data: bytes):
        if not self._conn:
            raise RuntimeError("Serial chua duoc mo. Goi open() truoc.")
        self._conn.write(data)

    def read_line(self) -> bytes:
        if not self._conn:
            raise RuntimeError("Serial chua duoc mo. Goi open() truoc.")
        return self._conn.readline()

    def close(self):
        if self._conn and self._conn.is_open:
            self._conn.close()
