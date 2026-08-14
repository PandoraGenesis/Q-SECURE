"""
config_local.example.py — MAU de tao file cau hinh rieng cho tung may.

Cach dung:
  1. Copy file nay thanh `config_local.py` (cung thu muc goc).
  2. Sua cac gia tri ben duoi cho DUNG voi may dang chay.
  3. KHONG commit `config_local.py` len Git (da co san trong .gitignore).

Vi du cho MAY HA (Alice):
------------------------------------------------
    from config import Role
    DEVICE_ROLE = Role.ALICE
    SERIAL_CONFIG = {
        "COM_PORT": "COM5",
        "BAUD_RATE": 115200,
        "SERIAL_TIMEOUT": 1,
    }

Vi du cho MAY SON (Bob):
------------------------------------------------
    from config import Role
    DEVICE_ROLE = Role.BOB
    NETWORK_CONFIG = {
        "HOST_BOB": "192.168.1.10",   # IP cua chinh may Bob
        "TCP_PORT": 5050,
        "BUFFER_SIZE": 4096,
        "SOCKET_TIMEOUT": 10,
    }
"""
