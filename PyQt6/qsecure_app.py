"""
qsecure_app.py
===============
Phan mem giao dien do hoa HOAN CHINH cho du an Q-SECURE, tich hop ca
4 module da xay dung rieng le truoc do:
    - esp32_serial.py  (SerialManager)   -> dieu khien Servo qua USB
    - qkd_logic.py     (sift_keys, calculate_qber) -> logic BB84
    - image_crypto.py  (encrypt_image, decrypt_image) -> ma hoa anh XOR
    - TCP Socket (module chuan socket cua Python) -> kenh truyen giua 2 may

Chay file nay TREN CA HAI MAY (Ha va Son), chi khac o phan chon vai
tro (Alice/Bob) va thong tin IP/Port trong bang dieu khien.

Yeu cau cai dat: PyQt6, opencv-python, numpy, pyserial (xem
requirements.txt cua du an). Dat file nay CUNG THU MUC voi 3 file
esp32_serial.py / qkd_logic.py / image_crypto.py da co san.

QUY UOC GIAO THUC (don gian hoa cho muc dich mo phong/hoc tap, xem
chu thich chi tiet trong ham run_alice_flow() / handle_bob_message()):
  1. Alice (vai Server) sinh bit+basis ngau nhien, gui day GOC SERVO
     (khong phai bit/basis) sang Bob - goc chinh la "tin hieu vat ly"
     duoc truyen di, giong cach anh sang phan cuc mang thong tin trong
     BB84 that.
  2. Bob doc goc, tu sinh basis rieng, "do" (measure) ra bit cua minh,
     gui LAI basis va bit-da-sift cua Bob cho Alice.
  3. Alice tinh QBER bang qkd_logic.calculate_qber(), ma hoa anh bang
     khoa cuoi cung, gui ca anh ma hoa LAN khoa cuoi cung cho Bob.
     (Trong BB84 that, khoa khong bao gio duoc gui qua kenh cong khai
     - o day gui kem de don gian hoa demo mot may/mot phien, KHONG
     phai thiet ke bao mat that su. Xem README de biet gioi han nay.)
  4. Bob nhan, tu giai ma bang image_crypto.decrypt_image(), hien thi
     ca 3 anh (goc/ma hoa/giai ma) va QBER len giao dien cua minh.
"""
import json
import random
import socket
import struct
import sys
import threading

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
    QSpinBox, QVBoxLayout, QWidget,
)

from esp32_serial import SerialConnectionError, SerialManager, list_available_ports
from image_crypto import decrypt_image, encrypt_image
from qkd_logic import calculate_qber, sift_keys

QBER_THRESHOLD = 11.0          # % - nguong an toan chuan BB84
VALID_ANGLES = (0, 45, 90, 135)


# ============================================================
# HAM TIEN ICH DUNG CHUNG
# ============================================================
def angle_for(basis: str, bit: int) -> int:
    """Anh xa (basis, bit) -> goc servo - PHAI khop dung VALID_ANGLES ben firmware ESP32."""
    if basis == "+":
        return 0 if bit == 0 else 90
    return 45 if bit == 0 else 135


def basis_bit_from_angle(angle: int):
    """Chieu nguoc lai: suy ra (basis, bit) tu 1 goc da nhan duoc."""
    mapping = {0: ("+", 0), 90: ("+", 1), 45: ("x", 0), 135: ("x", 1)}
    return mapping[angle]


def measure(sent_basis: str, sent_bit: int, measure_basis: str) -> int:
    """
    Mo phong phep do luong tu: do dung basis -> luon ra dung bit da
    gui; do sai basis -> ket qua ngau nhien 50/50, dung nguyen ly
    "khong nhan ban" cua BB84 (xem lai phan ly thuyet tren trang web
    du an de biet chi tiet).
    """
    if sent_basis == measure_basis:
        return sent_bit
    return random.randint(0, 1)


def cv2_image_to_qpixmap(image_bgr: np.ndarray) -> QPixmap:
    """Chuyen ma tran anh OpenCV (BGR, uint8) thanh QPixmap de hien thi len QLabel."""
    if image_bgr.ndim == 2:
        image_bgr = cv2.cvtColor(image_bgr, cv2.COLOR_GRAY2BGR)
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    rgb = np.ascontiguousarray(rgb)
    h, w, ch = rgb.shape
    qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
    # .copy() de QPixmap khong con tro toi bo nho numpy se bi giai phong
    # ngay sau khi ham nay ket thuc (numpy array la bien cuc bo).
    return QPixmap.fromImage(qimg.copy())


# ============================================================
# KHUNG DONG GOI/GIAI GOI BAN TIN QUA TCP
# Dinh dang: 4 byte do dai (big-endian) + noi dung JSON (UTF-8).
# Du lieu nhi phan (anh, khoa) duoc ma hoa hex trong JSON cho don gian.
# ============================================================
def _send_json(sock: socket.socket, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    sock.sendall(struct.pack(">I", len(data)) + data)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Kết nối bị đóng giữa chừng khi đang nhận dữ liệu.")
        buf.extend(chunk)
    return bytes(buf)


def _recv_json(sock: socket.socket) -> dict:
    header = _recv_exact(sock, 4)
    length = struct.unpack(">I", header)[0]
    payload = _recv_exact(sock, length)
    return json.loads(payload.decode("utf-8"))


# ============================================================
# LUONG MANG (QThread) - dung chung cho ca vai Alice (server) va
# Bob (client), tach biet khoi giao dien chinh de khong bi dong bang
# trong luc cho ket noi/nhan du lieu.
# ============================================================
class NetworkWorker(QThread):
    connected = pyqtSignal(str)          # dia chi doi phuong, vd "192.168.1.5:53210"
    message_received = pyqtSignal(dict)  # 1 ban tin JSON da nhan duoc tron ven
    error_occurred = pyqtSignal(str)
    disconnected = pyqtSignal()

    def __init__(self, role: str, bind_or_target_ip: str, port: int, parent=None):
        super().__init__(parent)
        self.role = role  # "Alice" -> lam server (listen), "Bob" -> lam client (connect)
        self.ip = bind_or_target_ip
        self.port = port
        self._sock: socket.socket | None = None
        self._server_sock: socket.socket | None = None
        self._running = False
        self._send_lock = threading.Lock()

    def run(self):
        self._running = True
        try:
            if self.role == "Alice":
                self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self._server_sock.bind((self.ip, self.port))
                self._server_sock.listen(1)
                self._sock, addr = self._server_sock.accept()
            else:
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._sock.settimeout(8)
                self._sock.connect((self.ip, self.port))
                self._sock.settimeout(None)
                addr = (self.ip, self.port)

            self.connected.emit(f"{addr[0]}:{addr[1]}")
        except OSError as e:
            self.error_occurred.emit(f"Không thể thiết lập kết nối mạng: {e}")
            return

        while self._running:
            try:
                msg = _recv_json(self._sock)
            except (ConnectionError, OSError):
                if self._running:
                    self.disconnected.emit()
                break
            self.message_received.emit(msg)

    def send(self, payload: dict) -> bool:
        """Goi TU LUONG CHINH (khong phai tu ben trong run()) de gui 1 ban tin di."""
        if self._sock is None:
            return False
        with self._send_lock:
            try:
                _send_json(self._sock, payload)
                return True
            except OSError as e:
                self.error_occurred.emit(f"Lỗi gửi dữ liệu qua mạng: {e}")
                return False

    def stop(self):
        self._running = False
        for s in (self._sock, self._server_sock):
            if s is not None:
                try:
                    s.close()
                except OSError:
                    pass
        self.wait(2000)


# ============================================================
# LUONG SERIAL (QThread) - dieu khien Servo qua ESP32. Neu khong
# chon cong COM (hoac khong co phan cung that), phan mem VAN CHAY
# DUOC binh thuong o che do chi mo phong phan mem - servo la PHU
# THEM cho truc quan, khong phai nguon du lieu quyet dinh bit/QBER.
# ============================================================
class SerialWorker(QThread):
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, port: str, angles_to_send, parent=None):
        super().__init__(parent)
        self.port = port
        self.angles_to_send = list(angles_to_send)
        self.manager: SerialManager | None = None

    def run(self):
        if not self.port:
            self.status_changed.emit("Không chọn cổng COM — bỏ qua điều khiển Servo thật.")
            return
        try:
            self.manager = SerialManager(port=self.port)
            self.manager.connect()
        except SerialConnectionError as e:
            self.error_occurred.emit(f"Không kết nối được ESP32: {e}")
            return

        for angle in self.angles_to_send:
            try:
                self.manager.send_servo_angle(angle)
            except Exception as e:  # noqa: BLE001 - khong de 1 loi lam dung ca chuoi truyen
                self.error_occurred.emit(f"Lỗi gửi lệnh Servo góc {angle}°: {e}")
        self.manager.disconnect()
        self.status_changed.emit("Đã gửi xong toàn bộ lệnh góc quay tới Servo thật.")


# ============================================================
# CUA SO CHINH
# ============================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Q-SECURE — Phần mềm điều khiển")
        self.resize(1040, 720)

        self.network_worker: NetworkWorker | None = None
        self.serial_worker: SerialWorker | None = None

        self.alice_bits = []
        self.alice_bases = []
        self.image_path = None
        self.original_image_shape = None
        self.flash_state = False

        self._build_ui()
        self._wire_events()

        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self._toggle_flash)

    # ---------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # ---- Bang dieu khien ----
        control_box = QGroupBox("Bảng điều khiển")
        control_layout = QVBoxLayout(control_box)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Vai trò:"))
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Alice (Máy Hà — gửi)", "Bob (Máy Sơn — nhận)"])
        row1.addWidget(self.role_combo)

        row1.addWidget(QLabel("Cổng COM:"))
        self.com_combo = QComboBox()
        self.com_combo.addItem("(Không dùng phần cứng)")
        row1.addWidget(self.com_combo)
        self.refresh_com_btn = QPushButton("Làm mới")
        row1.addWidget(self.refresh_com_btn)
        control_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Địa chỉ IP:"))
        self.ip_input = QLineEdit("127.0.0.1")
        row2.addWidget(self.ip_input)
        row2.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit("5050")
        row2.addWidget(self.port_input)
        row2.addWidget(QLabel("Số bit thô:"))
        self.nbits_input = QSpinBox()
        self.nbits_input.setRange(8, 4096)
        self.nbits_input.setValue(256)
        row2.addWidget(self.nbits_input)
        control_layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.select_image_btn = QPushButton("Chọn ảnh gốc…")
        row3.addWidget(self.select_image_btn)
        self.image_path_label = QLabel("(chưa chọn ảnh)")
        row3.addWidget(self.image_path_label, stretch=1)
        self.start_btn = QPushButton("Bắt đầu truyền tin")
        self.start_btn.setStyleSheet("font-weight:bold;")
        row3.addWidget(self.start_btn)
        control_layout.addLayout(row3)

        root.addWidget(control_box)

        # ---- Semaphore + 3 anh ----
        image_row = QHBoxLayout()

        self.semaphore_label = QLabel("Chưa có\ngóc nào")
        self.semaphore_label.setFixedSize(140, 140)
        self.semaphore_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.semaphore_label.setStyleSheet("border:1px solid #888; background:#0b2544; color:#dce8ea;")
        sema_box = QVBoxLayout()
        sema_box.addWidget(QLabel("Góc servo hiện tại"))
        sema_box.addWidget(self.semaphore_label)
        image_row.addLayout(sema_box)

        self.panel_labels = {}
        for key, caption in [("original", "Ảnh gốc"), ("encrypted", "Ảnh mã hoá"), ("decrypted", "Ảnh giải mã")]:
            box = QVBoxLayout()
            box.addWidget(QLabel(caption))
            lbl = QLabel("—")
            lbl.setFixedSize(220, 220)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("border:1px solid #888;")
            box.addWidget(lbl)
            self.panel_labels[key] = lbl
            image_row.addLayout(box)

        root.addLayout(image_row)

        # ---- Nhan QBER to, canh bao nhap nhay ----
        self.qber_label = QLabel("QBER: — %")
        self.qber_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qber_label.setFont(QFont("Consolas", 32, QFont.Weight.Bold))
        self.qber_label.setStyleSheet("padding:12px; border:2px solid #888;")
        root.addWidget(self.qber_label)

        # ---- Log ----
        root.addWidget(QLabel("Log tiến trình (sifting, mạng, phần cứng):"))
        self.log_console = QPlainTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumBlockCount(2000)
        root.addWidget(self.log_console, stretch=1)

        self._refresh_com_ports()

    # ---------------------------------------------------------------
    def _wire_events(self):
        self.refresh_com_btn.clicked.connect(self._refresh_com_ports)
        self.select_image_btn.clicked.connect(self._choose_image)
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.role_combo.currentIndexChanged.connect(self._on_role_changed)
        self._on_role_changed()

    def _on_role_changed(self):
        is_alice = self.role_combo.currentIndex() == 0
        self.select_image_btn.setEnabled(is_alice)
        self.nbits_input.setEnabled(is_alice)

    # ---------------------------------------------------------------
    def log(self, text: str):
        self.log_console.appendPlainText(text)

    def _refresh_com_ports(self):
        self.com_combo.clear()
        self.com_combo.addItem("(Không dùng phần cứng)")
        for p in list_available_ports():
            self.com_combo.addItem(p)

    def _choose_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn ảnh gốc", "", "Ảnh (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.image_path = path
            self.image_path_label.setText(path)
            pix = QPixmap(path)
            if not pix.isNull():
                self.panel_labels["original"].setPixmap(
                    pix.scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatio)
                )

    def set_semaphore_angle(self, angle: int):
        self.semaphore_label.setText(f"{angle}°")

    # ---------------------------------------------------------------
    def _toggle_flash(self):
        self.flash_state = not self.flash_state
        if self.flash_state:
            self.qber_label.setStyleSheet("padding:12px; border:2px solid red; background:#ff4444; color:white;")
        else:
            self.qber_label.setStyleSheet("padding:12px; border:2px solid red; background:#220000; color:#ff8888;")

    def update_qber_display(self, qber_percent: float):
        if qber_percent > QBER_THRESHOLD:
            self.qber_label.setText("⚠ CẢNH BÁO HACKER (EVE) ⚠")
            if not self.flash_timer.isActive():
                self.flash_timer.start(400)
        else:
            self.flash_timer.stop()
            self.qber_label.setStyleSheet("padding:12px; border:2px solid #2ecc71; background:#0b2544; color:#2ecc71;")
            self.qber_label.setText(f"QBER: {qber_percent:.2f} %  (an toàn)")

    # ---------------------------------------------------------------
    def _on_start_clicked(self):
        try:
            port = int(self.port_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Lỗi", "Port phải là số nguyên.")
            return
        ip = self.ip_input.text().strip()
        role = "Alice" if self.role_combo.currentIndex() == 0 else "Bob"

        if role == "Alice" and not self.image_path:
            QMessageBox.warning(self, "Lỗi", "Vai trò Alice cần chọn ảnh gốc trước khi bắt đầu.")
            return

        self.start_btn.setEnabled(False)
        self.log(f"[{role}] Đang thiết lập kết nối mạng tới {ip}:{port} ...")

        self.network_worker = NetworkWorker(role, ip, port)
        self.network_worker.connected.connect(self._on_network_connected)
        self.network_worker.message_received.connect(self._on_message_received)
        self.network_worker.error_occurred.connect(self._on_network_error)
        self.network_worker.disconnected.connect(lambda: self.log("[Mạng] Đối phương đã ngắt kết nối."))
        self.network_worker.start()

    def _on_network_error(self, msg: str):
        self.log(f"[Lỗi mạng] {msg}")
        self.start_btn.setEnabled(True)

    def _on_network_connected(self, addr: str):
        role = "Alice" if self.role_combo.currentIndex() == 0 else "Bob"
        self.log(f"[{role}] Đã kết nối mạng với {addr}.")
        if role == "Alice":
            self._run_alice_flow()

    # ---------------------------------------------------------------
    # LUONG XU LY BEN ALICE
    # ---------------------------------------------------------------
    def _run_alice_flow(self):
        n = self.nbits_input.value()
        self.log(f"[Alice] Sinh {n} bit + basis ngẫu nhiên...")

        self.alice_bits = [random.randint(0, 1) for _ in range(n)]
        self.alice_bases = [random.choice(["+", "x"]) for _ in range(n)]
        angles = [angle_for(b, v) for b, v in zip(self.alice_bases, self.alice_bits)]

        com_port = self.com_combo.currentText()
        if com_port != "(Không dùng phần cứng)":
            self.log(f"[Alice] Gửi {n} lệnh góc quay tới Servo thật qua {com_port}...")
            self.serial_worker = SerialWorker(com_port, angles)
            self.serial_worker.status_changed.connect(self.log)
            self.serial_worker.error_occurred.connect(lambda m: self.log(f"[Serial] {m}"))
            self.serial_worker.start()
        else:
            self.log("[Alice] Không dùng phần cứng thật — chỉ mô phỏng phần mềm.")

        if angles:
            self.set_semaphore_angle(angles[-1])

        self.log("[Alice] Gửi chuỗi góc (kênh quang mô phỏng) sang Bob qua mạng...")
        self.network_worker.send({"type": "angles", "angles": angles})

    # ---------------------------------------------------------------
    # BAT SU KIEN NHAN BAN TIN (dung chung cho ca 2 vai)
    # ---------------------------------------------------------------
    def _on_message_received(self, msg: dict):
        role = "Alice" if self.role_combo.currentIndex() == 0 else "Bob"
        msg_type = msg.get("type")

        if role == "Bob" and msg_type == "angles":
            self._bob_handle_angles(msg["angles"])
        elif role == "Alice" and msg_type == "bob_sifted":
            self._alice_handle_bob_sifted(msg["bob_bases"], msg["bob_sifted"])
        elif role == "Bob" and msg_type == "final_payload":
            self._bob_handle_final_payload(msg)
        else:
            self.log(f"[Cảnh báo] Nhận bản tin không xác định: {msg_type}")

    # ---------------------------------------------------------------
    # XU LY BEN BOB - buoc 1: nhan goc, tu "do", gui lai basis+bit sift
    # ---------------------------------------------------------------
    def _bob_handle_angles(self, angles):
        n = len(angles)
        self.log(f"[Bob] Nhận {n} góc từ Alice. Đang tự sinh basis và đo...")

        bob_bases = [random.choice(["+", "x"]) for _ in range(n)]
        alice_bases_derived = []
        bob_bits = []
        for angle, bb in zip(angles, bob_bases):
            sent_basis, sent_bit = basis_bit_from_angle(angle)
            alice_bases_derived.append(sent_basis)
            bob_bits.append(measure(sent_basis, sent_bit, bb))

        if angles:
            self.set_semaphore_angle(angles[-1])

        # bob_bits dung 2 lan lam "alice_bits" gia (khong quan trong,
        # xem chu thich trong sift_keys() - chi can ket qua *_sifted
        # dung phia cua chinh minh la du).
        _, bob_sifted, matched = sift_keys(alice_bases_derived, bob_bases, bob_bits, bob_bits)
        self.log(f"[Bob] Sifting xong: giữ {len(bob_sifted)}/{n} bit (basis trùng khớp).")

        self.network_worker.send({
            "type": "bob_sifted",
            "bob_bases": bob_bases,
            "bob_sifted": bob_sifted,
        })
        self.log("[Bob] Đã gửi lại basis + khoá thô cho Alice để đối chiếu QBER.")

    # ---------------------------------------------------------------
    # XU LY BEN ALICE - buoc 2: nhan basis+bit tho cua Bob, tinh QBER,
    # ma hoa anh, gui ket qua cuoi cung.
    # ---------------------------------------------------------------
    def _alice_handle_bob_sifted(self, bob_bases, bob_sifted):
        alice_sifted, _, matched = sift_keys(self.alice_bases, bob_bases, self.alice_bits, self.alice_bits)
        self.log(f"[Alice] Sifting xong: giữ {len(alice_sifted)} bit trùng basis.")

        n_common = min(len(alice_sifted), len(bob_sifted))
        qber, final_key = calculate_qber(alice_sifted[:n_common], bob_sifted[:n_common], sample_ratio=0.2)
        self.log(f"[Alice] QBER ước lượng: {qber:.2f}% — khoá bí mật còn lại: {len(final_key)} bit.")
        self.update_qber_display(qber)

        if qber > QBER_THRESHOLD:
            self.log("[Alice] QBER vượt ngưỡng an toàn — HUỶ khoá, KHÔNG gửi ảnh.")
            self.network_worker.send({"type": "final_payload", "aborted": True, "qber": qber})
            self.start_btn.setEnabled(True)
            return

        if not final_key:
            self.log("[Alice] Khoá cuối cùng rỗng (không đủ bit sau khi lấy mẫu) — không thể mã hoá ảnh.")
            self.start_btn.setEnabled(True)
            return

        self.log("[Alice] Đang mã hoá ảnh gốc bằng khoá vừa sift...")
        enc_matrix, enc_bytes, shape = encrypt_image(self.image_path, final_key)
        self.panel_labels["encrypted"].setPixmap(
            cv2_image_to_qpixmap(enc_matrix).scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatio)
        )

        # Tu giai ma lai o chinh phia Alice de kiem chung ngay tai cho
        # (khong bat buoc theo giao thuc, nhung giup xac nhan truc quan
        # rang khoa dung truoc khi gui di).
        dec_matrix, _ = decrypt_image(enc_bytes, final_key, shape)
        self.panel_labels["decrypted"].setPixmap(
            cv2_image_to_qpixmap(dec_matrix).scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatio)
        )

        self.log("[Alice] Đang gửi ảnh đã mã hoá + khoá cuối cùng sang Bob...")
        self.network_worker.send({
            "type": "final_payload",
            "aborted": False,
            "qber": qber,
            "encrypted_hex": enc_bytes.hex(),
            "shape": list(shape),
            "final_key": final_key,
        })
        self.log("[Alice] Hoàn tất phiên truyền tin.")
        self.start_btn.setEnabled(True)

    # ---------------------------------------------------------------
    # XU LY BEN BOB - buoc 3: nhan anh ma hoa + khoa, tu giai ma, hien thi
    # ---------------------------------------------------------------
    def _bob_handle_final_payload(self, msg: dict):
        qber = msg.get("qber", 0.0)
        self.update_qber_display(qber)

        if msg.get("aborted"):
            self.log(f"[Bob] Alice đã HUỶ phiên truyền — QBER {qber:.2f}% vượt ngưỡng an toàn.")
            self.start_btn.setEnabled(True)
            return

        shape = tuple(msg["shape"])
        enc_bytes = bytes.fromhex(msg["encrypted_hex"])
        final_key = msg["final_key"]

        self.log(f"[Bob] Nhận ảnh mã hoá ({len(enc_bytes)} byte) — QBER {qber:.2f}%. Đang giải mã...")

        enc_matrix = np.frombuffer(enc_bytes, dtype=np.uint8).reshape(shape)
        self.panel_labels["encrypted"].setPixmap(
            cv2_image_to_qpixmap(enc_matrix).scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatio)
        )

        dec_matrix, _ = decrypt_image(enc_bytes, final_key, shape)
        self.panel_labels["decrypted"].setPixmap(
            cv2_image_to_qpixmap(dec_matrix).scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatio)
        )
        self.panel_labels["original"].setPixmap(
            cv2_image_to_qpixmap(dec_matrix).scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatio)
        )
        self.log("[Bob] Giải mã xong, hiển thị kết quả. Hoàn tất phiên truyền tin.")
        self.start_btn.setEnabled(True)

    # ---------------------------------------------------------------
    def closeEvent(self, event):
        if self.network_worker is not None:
            self.network_worker.stop()
        if self.serial_worker is not None:
            self.serial_worker.wait(1000)
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
