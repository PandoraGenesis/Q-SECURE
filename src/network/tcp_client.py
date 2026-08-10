"""
tcp_client.py — (May Alice) Ket noi toi may Bob va gui du lieu
(anh da XOR + metadata) qua TCP Socket.
"""
import socket

from config import NETWORK_CONFIG


class TcpClient:
    def __init__(self, host: str = NETWORK_CONFIG["HOST_BOB"], port: int = NETWORK_CONFIG["TCP_PORT"]):
        self.host = host
        self.port = port
        self._sock: socket.socket | None = None

    def connect(self):
        raise NotImplementedError

    def send_data(self, payload: bytes):
        """Dong goi bang protocol_utils.pack_message() roi gui di."""
        raise NotImplementedError

    def close(self):
        if self._sock:
            self._sock.close()
