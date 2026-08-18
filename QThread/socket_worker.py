"""
socket_worker.py
==================
SocketWorker(QThread) - luong PyQt6 doc lap, chay ben duoi giao dien
chinh de lang nghe/nhan du lieu goi tin (anh da ma hoa) qua TCP
Socket ma khong lam dong bang giao dien trong luc cho ket noi/du lieu.

Dinh dang khung du lieu: 4 byte dau (big-endian) the hien do dai phan
con lai, roi den dung day so byte do la noi dung nhi phan (vd anh da
ma hoa bang XOR) - nho co header nay, worker biet chinh xac khi nao
1 "khung anh" da nhan tron ven de phat tin hieu, thay vi phat ngau
nhien theo tung goi TCP nho le (TCP khong dam bao 1 lan send() khop
voi 1 lan recv() ben nhan).

Ho tro ca 2 vai tro qua tham so `mode`:
    - mode="server": mo cong, lang nghe, cho 1 ket noi den (dung cho
      tram Alice - ben gui - trong kien truc Hermex).
    - mode="client": chu dong ket noi toi dia chi cho san (dung cho
      tram Bob - ben nhan).
"""
import socket
import struct
import threading
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

HEADER_SIZE = 4          # so byte cua truong do dai dat truoc moi khung du lieu
CONNECT_TIMEOUT_S = 10    # timeout khi o vai client dang ket noi toi server


class SocketWorker(QThread):
    """
    Lang nghe/nhan du lieu qua TCP Socket tren mot QThread rieng. Moi
    khung du lieu hoan chinh (dung do dai da khai bao trong 4 byte
    header) se phat tin hieu image_received(bytes). Moi buoc trong
    tien trinh ket noi (dang cho, da ket noi, mat ket noi, loi...)
    deu bao qua status_changed(str) de GUI hien thi ro rang.
    """

    image_received = pyqtSignal(bytes)
    status_changed = pyqtSignal(str)

    def __init__(self, mode: str, host: str, port: int, parent=None):
        super().__init__(parent)
        if mode not in ("server", "client"):
            raise ValueError("mode phải là 'server' hoặc 'client'.")
        self.mode = mode
        self.host = host
        self.port = port
        self._sock: Optional[socket.socket] = None
        self._server_sock: Optional[socket.socket] = None
        self._running = False
        self._send_lock = threading.Lock()

    def run(self):
        self._running = True

        try:
            if self.mode == "server":
                self.status_changed.emit(f"Đang chờ kết nối trên {self.host}:{self.port}...")
                self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self._server_sock.bind((self.host, self.port))
                self._server_sock.listen(1)
                self._sock, addr = self._server_sock.accept()
            else:
                self.status_changed.emit(f"Đang kết nối tới {self.host}:{self.port}...")
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._sock.settimeout(CONNECT_TIMEOUT_S)
                self._sock.connect((self.host, self.port))
                self._sock.settimeout(None)  # bo timeout sau khi da ket noi, de recv() cho binh thuong khong bi ngat ngang
                addr = (self.host, self.port)
        except socket.timeout:
            self.status_changed.emit(f"[Lỗi] Hết thời gian chờ kết nối tới {self.host}:{self.port}.")
            return
        except OSError as e:
            self.status_changed.emit(f"[Lỗi] Không thể thiết lập kết nối mạng: {e}")
            return

        self.status_changed.emit(f"Đã kết nối với {addr[0]}:{addr[1]}")

        while self._running:
            try:
                frame = self._receive_one_frame()
            except ConnectionError as e:
                if self._running:
                    self.status_changed.emit(f"Đối phương đã ngắt kết nối: {e}")
                break
            except OSError as e:
                if self._running:
                    self.status_changed.emit(f"[Lỗi] Sự cố mạng khi đang nhận dữ liệu: {e}")
                break

            self.image_received.emit(frame)

        self._close_sockets()

    def _receive_one_frame(self) -> bytes:
        header = self._recv_exact(HEADER_SIZE)
        (length,) = struct.unpack(">I", header)
        return self._recv_exact(length)

    def _recv_exact(self, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("kết nối bị đóng giữa chừng khi đang nhận dữ liệu.")
            buf.extend(chunk)
        return bytes(buf)

    def send_bytes(self, payload: bytes) -> bool:
        """
        Goi TU LUONG CHINH (GUI) de gui 1 khung du lieu (vd anh da ma
        hoa) di, tu dong them dung header 4-byte do dai o truoc. Dung
        khoa rieng (_send_lock) de tranh xung dot neu co nhieu noi
        cung goi gui gan nhu dong thoi.
        """
        if self._sock is None:
            return False
        with self._send_lock:
            try:
                header = struct.pack(">I", len(payload))
                self._sock.sendall(header + payload)
                return True
            except OSError as e:
                self.status_changed.emit(f"[Lỗi] Gửi dữ liệu qua mạng thất bại: {e}")
                return False

    def _close_sockets(self):
        """
        QUAN TRONG: goi shutdown() TRUOC close() cho socket dang ket
        noi (self._sock). Neu chi goi close() truc tiep tu ben ngoai
        trong luc luong nay dang bi chan (block) o ben trong recv()
        tren CHINH socket do, ca 2 co the bi treo vinh vien - day la
        cam bay kinh dien cua lap trinh da luong voi socket tren POSIX
        (da tu kiem chung bang socket thuan, khong dinh PyQt6, truoc
        khi sua). shutdown(SHUT_RDWR) duoc thiet ke rieng de an toan
        khi goi tu luong khac nham "danh thuc" mot cuoc goi recv()
        dang bi chan, sau do close() moi thuc su giai phong file
        descriptor ma khong con rui ro nay.
        """
        if self._sock is not None:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass  # socket co the da o trang thai khong con shutdown duoc (da dong tu truoc, loi mang...)
            try:
                self._sock.close()
            except OSError:
                pass

        if self._server_sock is not None:
            try:
                self._server_sock.close()
            except OSError:
                pass

    def stop(self):
        """Goi TU LUONG CHINH (GUI) de dung worker mot cach an toan."""
        self._running = False
        self._close_sockets()
        self.wait(2000)
