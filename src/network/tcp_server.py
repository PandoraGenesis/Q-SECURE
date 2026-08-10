"""
tcp_server.py — (May Bob) Lang nghe ket noi TCP tu Alice, nhan du
lieu (anh ma hoa + metadata sifting/QBER) theo dinh dang o
protocol_utils.py.
"""
import socket

from config import NETWORK_CONFIG


class TcpServer:
    def __init__(self, host: str = "0.0.0.0", port: int = NETWORK_CONFIG["TCP_PORT"]):
        self.host = host
        self.port = port
        self._sock: socket.socket | None = None

    def start(self):
        """Mo socket, bind va listen. Goi trong QThread worker rieng."""
        raise NotImplementedError

    def receive_data(self) -> bytes:
        """Nhan du lieu theo khung protocol_utils (header 4 byte + payload)."""
        raise NotImplementedError

    def close(self):
        if self._sock:
            self._sock.close()
