"""
network_worker.py — Chay TcpServer/TcpClient tren mot QThread rieng
de KHONG lam dong/treo giao dien chinh khi cho du lieu mang.
"""
from PyQt6.QtCore import QThread, pyqtSignal


class NetworkWorker(QThread):
    data_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self, role, parent=None):
        super().__init__(parent)
        self.role = role  # Role.ALICE hoac Role.BOB

    def run(self):
        """
        Neu role la BOB: khoi tao TcpServer, listen, emit data_received
        moi khi nhan xong 1 goi tin.
        Neu role la ALICE: khoi tao TcpClient, ket noi va gui du lieu
        (du lieu duoc truyen vao qua ham rieng truoc khi start()).
        """
        raise NotImplementedError
