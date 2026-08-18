"""
esp32_serial.py
================
Module GIAO TIẾP PHẦN CỨNG cho dự án Hermex. Dùng chung cho cả hai
máy: bên Alice để gửi lệnh Servo, bên Bob để lắng nghe dữ liệu LDR —
class SerialManager không tự biết vai trò, vai trò do code gọi nó
(vd SerialWorker) quyết định sẽ gọi send_servo_angle() hay chỉ đọc
get_latest_reading().

Chức năng chính:
    1. Mở/đóng kết nối Serial (USB) với ESP32 — cấu hình chuẩn baudrate 115200.
    2. Gửi lệnh điều khiển góc quay Servo (0 / 45 / 90 / 135 độ) xuống ESP32.
    3. Chạy một LUỒNG NỀN (background thread) liên tục lắng nghe dữ liệu cảm
       biến LDR mà ESP32 gửi trả về, KHÔNG làm đóng băng luồng chính (GUI).
    4. Xử lý ngoại lệ toàn diện: cổng COM không tồn tại, mất kết nối đột ngột
       (rút cáp USB), dữ liệu trả về sai định dạng / nhiễu tín hiệu.

Thiết kế có chủ đích:
    - Dùng threading.Thread (chuẩn thư viện Python) thay vì QThread của PyQt6
      để module này KHÔNG phụ thuộc framework GUI cụ thể nào — có thể tái sử
      dụng độc lập, dễ unit-test, và lớp GUI chỉ cần "bọc" nó lại (vd một
      QThread trong project gọi manager.get_latest_reading() theo chu kỳ).
    - Dùng queue.Queue để truyền dữ liệu giữa luồng đọc nền và luồng chính:
      đây là cấu trúc dữ liệu AN TOÀN LUỒNG (thread-safe) có sẵn trong Python,
      tự xử lý lock nội bộ nên không cần tự viết cơ chế đồng bộ thủ công.

Cách sử dụng cơ bản:
    manager = SerialManager(port="COM5")
    manager.connect()
    manager.start_listening()
    manager.send_servo_angle(90)

    reading = manager.get_latest_reading(timeout=1.0)
    if reading:
        print(reading.ldr_value)

    manager.disconnect()

Hoặc dùng với context manager (tự động connect/disconnect):
    with SerialManager(port="COM5") as manager:
        manager.send_servo_angle(45)
        ...
"""

import queue
import threading
import time
from dataclasses import dataclass
from typing import List, Optional

import serial
import serial.tools.list_ports

from config import SERIAL_CONFIG
from src.utils.logger import get_logger

# Dung chung 1 logger duoc cau hinh boi utils/logger.py (ghi ra ca
# console lan file logs/hermex.log) thay vi tu goi logging.basicConfig
# rieng - tranh xung dot cau hinh logging khi module nay duoc import
# tu ben trong ung dung GUI chinh.
logger = get_logger("hardware.esp32_serial")


# ======================================================================
# CÁC EXCEPTION TÙY CHỈNH
# Tách riêng từng loại lỗi giúp code gọi module này (và bản thân bạn khi
# giải trình phản biện) phân biệt rõ NGUYÊN NHÂN gốc của sự cố.
# ======================================================================
class SerialConnectionError(Exception):
    """Không thể MỞ được kết nối Serial (sai tên cổng COM, cổng bị chiếm dụng,
    hoặc mất kết nối đột ngột giữa chừng khi đang gửi/nhận dữ liệu)."""
    pass


class SerialNotConnectedError(Exception):
    """Gọi hàm gửi/nhận dữ liệu trong khi kết nối Serial CHƯA được mở
    (quên gọi connect(), hoặc kết nối đã bị đóng trước đó)."""
    pass


# ======================================================================
# CẤU TRÚC DỮ LIỆU: 1 BẢN GHI CẢM BIẾN
# ======================================================================
@dataclass
class SensorReading:
    """Đóng gói 1 giá trị cảm biến LDR đọc được từ ESP32, kèm mốc thời gian
    nhận và dòng dữ liệu thô gốc (phục vụ log/debug khi cần đối chiếu)."""
    ldr_value: int      # giá trị analog LDR (ADC ESP32: 0-4095 với độ phân giải 12-bit)
    timestamp: float    # thời điểm phần mềm NHẬN được dòng dữ liệu (time.time())
    raw_line: str        # dòng text thô gốc, vd "LDR:512"


# ======================================================================
# CLASS CHÍNH: SerialManager
# ======================================================================
class SerialManager:
    """
    Quản lý toàn bộ vòng đời kết nối Serial với ESP32: mở/đóng cổng, gửi lệnh
    điều khiển Servo, và chạy luồng nền đọc liên tục dữ liệu cảm biến LDR.
    """

    # Danh sách góc Servo hợp lệ theo thiết kế phần cứng của đề tài.
    # Đặt thành hằng số ở đây để dễ sửa/mở rộng và tránh "magic number" rải rác.
    VALID_SERVO_ANGLES = (0, 45, 90, 135)

    def __init__(
        self,
        port: str = SERIAL_CONFIG["COM_PORT"],
        baudrate: int = SERIAL_CONFIG["BAUD_RATE"],
        timeout: float = SERIAL_CONFIG["SERIAL_TIMEOUT"],
        write_timeout: float = 1.0,
        queue_maxsize: int = 200,
    ):
        """
        Khởi tạo đối tượng quản lý (CHƯA mở kết nối — phải gọi connect()).
        Giá trị mặc định của port/baudrate/timeout lấy từ SERIAL_CONFIG
        trong config.py (tự động phản ánh config_local.py của từng máy),
        có thể truyền tay để override khi cần.

        Args:
            port: tên cổng COM, vd "COM5" (Windows) hoặc "/dev/ttyUSB0" (Linux/macOS).
            baudrate: tốc độ truyền (bit/s), mặc định 115200 — PHẢI khớp với
                      giá trị Serial.begin(115200) được cấu hình trong firmware ESP32.
            timeout: số giây tối đa chờ khi ĐỌC dữ liệu trước khi trả về rỗng.
                     Giá trị này quan trọng vì nó là chu kỳ luồng đọc nền kiểm
                     tra cờ dừng (_stop_event) — timeout càng nhỏ, luồng dừng
                     càng nhanh khi gọi stop_listening(), nhưng CPU phải "thức
                     dậy" kiểm tra thường xuyên hơn.
            write_timeout: số giây tối đa chờ khi GHI dữ liệu (đề phòng buffer đầy).
            queue_maxsize: giới hạn số bản ghi tối đa lưu trong hàng đợi, tránh
                           tràn bộ nhớ nếu luồng chính (GUI) đọc chậm hơn tốc độ
                           ESP32 gửi dữ liệu lên.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.write_timeout = write_timeout

        self._conn: Optional[serial.Serial] = None
        self._read_thread: Optional[threading.Thread] = None

        # Cờ báo hiệu dừng luồng đọc một cách AN TOÀN (thay vì kill thread
        # đột ngột — cách làm không được khuyến khích và có thể để lại cổng
        # Serial ở trạng thái không nhất quán).
        self._stop_event = threading.Event()

        # Hàng đợi thread-safe: luồng đọc nền PUT dữ liệu vào đây, luồng
        # chính (GUI) GET dữ liệu ra — không cần tự viết lock vì queue.Queue
        # đã tự đảm bảo an toàn khi nhiều luồng truy cập đồng thời.
        self.data_queue: "queue.Queue[SensorReading]" = queue.Queue(maxsize=queue_maxsize)

        # Lock riêng bảo vệ thao tác GHI (write) xuống cổng Serial — phòng
        # trường hợp nhiều nơi trong GUI (vd nhiều nút bấm góc servo) gọi
        # send_servo_angle() gần như đồng thời từ các luồng khác nhau.
        self._write_lock = threading.Lock()

    # ------------------------------------------------------------------
    # 1. MỞ / ĐÓNG KẾT NỐI
    # ------------------------------------------------------------------
    def connect(self) -> None:
        """
        Mở kết nối Serial tới ESP32 với cấu hình chuẩn.

        Raises:
            SerialConnectionError: khi cổng COM không tồn tại, đang bị chương
                trình khác (vd Arduino IDE Serial Monitor) chiếm dụng, hoặc
                bất kỳ lỗi nào khác pyserial trả về khi mở cổng.
        """
        try:
            self._conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.write_timeout,
            )
            # Nhiều board ESP32/Arduino tự RESET khi cổng Serial vừa được mở
            # (do tín hiệu DTR bị toggle) — cần đợi vài giây để board boot lại
            # xong trước khi gửi lệnh, nếu không lệnh đầu tiên có thể bị mất.
            time.sleep(2.0)
            logger.info("Đã kết nối ESP32 tại %s (baudrate=%s)", self.port, self.baudrate)

        except serial.SerialException as e:
            logger.error("Không thể mở cổng %s: %s", self.port, e)
            raise SerialConnectionError(
                f"Không thể kết nối tới cổng {self.port}. Kiểm tra: "
                f"(1) ESP32 đã cắm cáp USB chưa, "
                f"(2) tên cổng COM có đúng không (dùng list_available_ports() để tra), "
                f"(3) cổng có đang bị phần mềm khác chiếm dụng không (vd Arduino IDE)."
            ) from e

    def disconnect(self) -> None:
        """Dừng luồng đọc nền (nếu đang chạy) rồi đóng kết nối Serial một cách an toàn."""
        self.stop_listening()
        if self._conn is not None and self._conn.is_open:
            self._conn.close()
            logger.info("Đã đóng kết nối Serial tại %s", self.port)
        self._conn = None

    def is_connected(self) -> bool:
        """Kiểm tra nhanh kết nối Serial hiện có đang mở hay không."""
        return self._conn is not None and self._conn.is_open

    # ------------------------------------------------------------------
    # 2. GỬI LỆNH ĐIỀU KHIỂN SERVO
    # ------------------------------------------------------------------
    def send_servo_angle(self, angle: int) -> None:
        """
        Gửi lệnh điều khiển góc quay Servo xuống ESP32.

        Định dạng khung lệnh (dạng text, kết thúc bằng ký tự xuống dòng):
            "<goc>\\n"     ví dụ: "90\\n"
        Chỉ gửi đúng số nguyên trần, KHÔNG có tiền tố chữ nào — khớp với
        firmware hiện tại của cả hai board (Alice lẫn Bob), vốn dùng
        isNumericString() để phân biệt số hợp lệ với dữ liệu rác.

        Args:
            angle: góc quay Servo — BẮT BUỘC thuộc VALID_SERVO_ANGLES (0/45/90/135).

        Raises:
            ValueError: nếu `angle` không nằm trong danh sách góc hợp lệ.
            SerialNotConnectedError: nếu chưa connect() hoặc kết nối đã đóng.
            SerialConnectionError: nếu quá trình ghi dữ liệu thất bại do lỗi
                phần cứng (vd rút cáp USB đúng lúc đang gửi lệnh).
        """
        if angle not in self.VALID_SERVO_ANGLES:
            raise ValueError(
                f"Góc {angle} không hợp lệ. Chỉ chấp nhận một trong: {self.VALID_SERVO_ANGLES}"
            )

        if not self.is_connected():
            raise SerialNotConnectedError(
                "Chưa kết nối tới ESP32 — gọi connect() trước khi gửi lệnh Servo."
            )

        command = f"{angle}\n".encode("utf-8")

        # Khóa (lock) thao tác ghi để tránh xung đột nếu có nhiều luồng cùng
        # gọi send_servo_angle() gần như đồng thời (vd nhiều nút bấm GUI).
        with self._write_lock:
            try:
                self._conn.write(command)
                self._conn.flush()  # đẩy dữ liệu đi ngay, không chờ buffer đầy
                logger.info("Đã gửi lệnh Servo: %s độ", angle)

            except serial.SerialException as e:
                # Trường hợp điển hình: cáp USB bị rút ra đột ngột trong khi ghi.
                logger.error("Mất kết nối khi gửi lệnh Servo: %s", e)
                raise SerialConnectionError(
                    "Mất kết nối Serial trong lúc gửi lệnh Servo "
                    "(có thể do cáp USB bị rút ra đột ngột)."
                ) from e

    # ------------------------------------------------------------------
    # 3. LUỒNG ĐỌC DỮ LIỆU NGẦM (BACKGROUND THREAD)
    # ------------------------------------------------------------------
    def start_listening(self) -> None:
        """
        Khởi động luồng nền liên tục đọc dữ liệu cảm biến LDR từ ESP32,
        KHÔNG chặn (block) luồng gọi hàm này — cho phép GUI chính vẫn phản
        hồi mượt mà trong lúc chờ dữ liệu Serial.
        """
        if not self.is_connected():
            raise SerialNotConnectedError("Phải connect() trước khi start_listening().")

        if self._read_thread is not None and self._read_thread.is_alive():
            logger.warning("Luồng đọc đã đang chạy — bỏ qua yêu cầu start_listening() trùng lặp.")
            return

        self._stop_event.clear()

        # daemon=True: đảm bảo luồng này tự động bị dừng khi chương trình
        # chính (main thread) thoát, không cần chờ join() thủ công nếu
        # người dùng đóng ứng dụng đột ngột (vd bấm dấu X trên cửa sổ).
        self._read_thread = threading.Thread(
            target=self._read_loop,
            name="SerialReadThread",
            daemon=True,
        )
        self._read_thread.start()
        logger.info("Đã khởi động luồng đọc dữ liệu cảm biến nền.")

    def stop_listening(self) -> None:
        """Báo hiệu dừng luồng đọc nền và ĐỢI (join) nó kết thúc hẳn trước khi trả về."""
        self._stop_event.set()
        if self._read_thread is not None and self._read_thread.is_alive():
            # Chờ tối đa (timeout + 1) giây — đủ thời gian để vòng lặp đọc
            # thoát ra sau lệnh readline() hiện tại, tránh join() treo vô hạn.
            self._read_thread.join(timeout=self.timeout + 1.0)
        self._read_thread = None

    def _read_loop(self) -> None:
        """
        Vòng lặp CHẠY TRONG LUỒNG NỀN: liên tục đọc từng dòng dữ liệu thô từ
        ESP32, parse thành SensorReading, rồi đẩy vào self.data_queue.

        Định dạng dòng dữ liệu ESP32 gửi lên (text, kết thúc bằng '\\n'):
            "LDR:<gia_tri_nguyen>\\n"    ví dụ: "LDR:512\\n"
        """
        while not self._stop_event.is_set():
            try:
                if self._conn is None or not self._conn.is_open:
                    # Kết nối đã bị đóng từ nơi khác (vd disconnect() gọi
                    # song song từ luồng chính) — dừng vòng lặp ngay.
                    break

                # readline() sẽ chờ TỐI ĐA `timeout` giây; nếu không có dữ
                # liệu mới sẽ trả về b"" (bytes rỗng) thay vì treo vô hạn —
                # đây chính là lý do timeout ở connect() rất quan trọng.
                raw_bytes = self._conn.readline()

                if not raw_bytes:
                    # Hết timeout mà không có dữ liệu — hoàn toàn bình
                    # thường (ESP32 có thể gửi không đều đặn), thử lại vòng sau.
                    continue

                self._handle_incoming_line(raw_bytes)

            except serial.SerialException as e:
                # Mất kết nối đột ngột trong lúc ĐANG ĐỌC (vd rút cáp USB
                # giữa chừng). KHÔNG raise exception ở đây vì đây là luồng
                # nền — raise sẽ chỉ làm luồng chết âm thầm mà luồng chính
                # không hay biết. Thay vào đó: log lỗi, dừng vòng lặp, để
                # luồng chính tự phát hiện qua is_connected().
                logger.error("Mất kết nối Serial trong luồng đọc nền: %s", e)
                break

            except Exception as e:  # noqa: BLE001
                # Bắt rộng có chủ đích: bất kỳ lỗi không lường trước nào
                # (vd lỗi lạ khi decode) cũng KHÔNG được làm chết hẳn luồng
                # đọc — chỉ log lại và tiếp tục đọc dòng kế tiếp.
                logger.error("Lỗi không xác định trong luồng đọc Serial: %s", e)
                continue

        logger.info("Luồng đọc dữ liệu cảm biến đã dừng hẳn.")

    def _handle_incoming_line(self, raw_bytes: bytes) -> None:
        """
        Parse 1 dòng dữ liệu thô (bytes) từ ESP32 thành SensorReading rồi đẩy
        vào hàng đợi. Được tách thành hàm riêng để dễ unit-test độc lập và dễ
        giải trình logic xử lý dữ liệu nhiễu khi phản biện đề tài.
        """
        # --- Bước 1: decode bytes -> string, bắt lỗi nhiễu ở TẦNG BYTE ---
        try:
            raw_line = raw_bytes.decode("utf-8", errors="strict").strip()
        except UnicodeDecodeError:
            # Nhiễu tín hiệu điện trên đường truyền UART có thể khiến 1 vài
            # byte bị sai lệch, làm chuỗi không còn là UTF-8 hợp lệ.
            logger.warning("Bỏ qua dòng dữ liệu lỗi encoding (nghi nhiễu tín hiệu): %r", raw_bytes)
            return

        if not raw_line:
            return  # dòng trắng, không cần xử lý

        # --- Bước 2: kiểm tra ĐỊNH DẠNG (tầng cấu trúc dữ liệu) ---
        if not raw_line.startswith("LDR:"):
            logger.warning("Bỏ qua dòng dữ liệu sai định dạng (không nhận diện được): %r", raw_line)
            return

        value_part = raw_line[len("LDR:"):]

        # --- Bước 3: kiểm tra KIỂU DỮ LIỆU của phần giá trị ---
        try:
            ldr_value = int(value_part)
        except ValueError:
            # Dữ liệu bị cắt/lỗi giữa chừng do nhiễu UART (vd "LDR:5\x0012"
            # thay vì "LDR:512") khiến phần giá trị không phải số nguyên hợp lệ.
            logger.warning("Bỏ qua dòng dữ liệu có giá trị LDR không hợp lệ: %r", raw_line)
            return

        reading = SensorReading(ldr_value=ldr_value, timestamp=time.time(), raw_line=raw_line)

        # --- Bước 4: đẩy vào hàng đợi thread-safe cho luồng chính lấy ra ---
        try:
            self.data_queue.put_nowait(reading)
        except queue.Full:
            # Nếu GUI đọc chậm hơn tốc độ ESP32 gửi dữ liệu lên, hàng đợi có
            # thể bị đầy. Chiến lược: loại bỏ bản ghi CŨ NHẤT để nhường chỗ
            # cho bản ghi MỚI — ưu tiên dữ liệu thời gian thực hơn dữ liệu cũ.
            try:
                self.data_queue.get_nowait()
                self.data_queue.put_nowait(reading)
            except queue.Empty:
                pass

    # ------------------------------------------------------------------
    # 4. API CHO LUỒNG CHÍNH (GUI) LẤY DỮ LIỆU RA KHỎI HÀNG ĐỢI
    # ------------------------------------------------------------------
    def get_latest_reading(self, timeout: Optional[float] = None) -> Optional[SensorReading]:
        """
        Lấy MỘT bản ghi cảm biến từ hàng đợi — gọi từ luồng chính (GUI).

        Args:
            timeout: số giây tối đa chờ nếu hàng đợi đang rỗng.
                     None -> trả về NGAY LẬP TỨC (non-blocking); nếu hàng đợi
                     rỗng, trả về None luôn (không chặn giao diện).

        Returns:
            SensorReading nếu có dữ liệu, ngược lại None.
        """
        try:
            if timeout is None:
                return self.data_queue.get_nowait()
            return self.data_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def drain_all_readings(self) -> List[SensorReading]:
        """
        Lấy TOÀN BỘ các bản ghi hiện có trong hàng đợi cùng lúc.
        Hữu ích khi GUI muốn vẽ biểu đồ/cập nhật hàng loạt theo mỗi khung hình
        (frame) thay vì xử lý từng bản ghi một, giảm số lần cập nhật giao diện.
        """
        readings: List[SensorReading] = []
        while True:
            try:
                readings.append(self.data_queue.get_nowait())
            except queue.Empty:
                break
        return readings

    # ------------------------------------------------------------------
    # HỖ TRỢ CONTEXT MANAGER: with SerialManager(...) as manager:
    # Giúp đảm bảo LUÔN đóng kết nối đúng cách kể cả khi có lỗi xảy ra
    # giữa chừng (tương tự cách dùng `with open(...) as f:` quen thuộc).
    # ------------------------------------------------------------------
    def __enter__(self) -> "SerialManager":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()


# ======================================================================
# HÀM TIỆN ÍCH: LIỆT KÊ CÁC CỔNG COM ĐANG CÓ TRÊN MÁY
# ======================================================================
def list_available_ports() -> List[str]:
    """
    Trả về danh sách tên các cổng COM đang khả dụng trên máy tính.
    Hữu ích để hiển thị dropdown chọn cổng trên GUI thay vì bắt người dùng gõ
    tay tên cổng — giảm đáng kể lỗi "cổng COM không tồn tại" do gõ sai.
    """
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]


# ======================================================================
# VÍ DỤ SỬ DỤNG ĐỘC LẬP — chạy thử module này riêng (không cần GUI/PyQt6)
# ======================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    print("Các cổng COM khả dụng:", list_available_ports())

    # Đổi "COM5" thành cổng thực tế của ESP32 trên máy bạn trước khi chạy thử.
    with SerialManager(port="COM5", baudrate=115200, timeout=1.0) as manager:
        manager.start_listening()
        manager.send_servo_angle(90)

        # Demo: đọc dữ liệu cảm biến liên tục trong 10 giây rồi thoát.
        start_time = time.time()
        while time.time() - start_time < 10:
            reading = manager.get_latest_reading(timeout=0.5)
            if reading is not None:
                print(f"[{reading.timestamp:.2f}] LDR = {reading.ldr_value}")
    # Khi thoát khỏi khối `with`, __exit__ tự động gọi disconnect() —
    # đảm bảo luồng đọc nền được dừng và cổng Serial được đóng gọn gàng.
