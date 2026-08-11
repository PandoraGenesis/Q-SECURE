"""
config.py — File cau hinh TRUNG TAM cho du an Q-SECURE.

Ca hai may (Alice va Bob) dung CHUNG file nay tu 1 repo Git duy nhat.
Cac gia tri rieng cho tung may (ROLE, COM_PORT, IP...) duoc GHI DE boi file `config_local.py` — file nay KHONG duoc dua len Git (xem
.gitignore), moi may tu tao rieng bang cach copy tu `config_local.example.py`.
"""

import os
from enum import Enum

# ============================================================
# 1. VAI TRO THIET BI (ROLE)
# ============================================================
class Role(Enum):
    ALICE = "ALICE"   # May gui (Ha)
    BOB = "BOB"        # May nhan (Son)

# Doc ROLE tu bien moi truong truoc, mac dinh ALICE neu chua cau hinh.
# Se bi ghi de boi config_local.py neu file do dinh nghia DEVICE_ROLE.
DEVICE_ROLE = Role(os.getenv("QSECURE_ROLE", "ALICE").upper())

# ============================================================
# 2. CAU HINH MANG (TCP SOCKET)
# ============================================================
NETWORK_CONFIG = {
    "HOST_BOB": "192.168.1.10",   # Dia chi IP cua may Bob trong mang LAN
    "TCP_PORT": 5050,             # Cong TCP dung de truyen du lieu
    "BUFFER_SIZE": 4096,          # Kich thuoc buffer nhan du lieu (bytes)
    "SOCKET_TIMEOUT": 10,         # Timeout ket noi (giay)
}

# ============================================================
# 3. CAU HINH PHAN CUNG (ESP32 - SERIAL)
# ============================================================
SERIAL_CONFIG = {
    "COM_PORT": "COM3",           # Cong COM mac dinh - THUONG PHAI DOI theo tung may
    "BAUD_RATE": 115200,
    "SERIAL_TIMEOUT": 1,          # giay
}

# ============================================================
# 4. THAM SO THUAT TOAN BB84 / SIFTING / QBER
# ============================================================
QKD_PARAMS = {
    "KEY_LENGTH_RAW": 512,        # So bit tho sinh ra ban dau
    "QBER_SAMPLE_RATIO": 0.2,     # Ty le bit dung de uoc luong loi (cong khai so sanh)
    "QBER_THRESHOLD": 0.11,       # Nguong QBER toi da chap nhan (chuan BB84 ~11%)
}

# ============================================================
# 5. DUONG DAN & TAI NGUYEN GIAO DIEN
# ============================================================
PATHS = {
    "ASSETS_DIR": "assets",
    "SAMPLE_IMAGE": "assets/sample_images/lena.png",
    "LOG_DIR": "logs",
}

# ============================================================
# 6. GHI DE CAU HINH RIENG CHO TUNG MAY (neu co)
#    -> Tao file config_local.py (copy tu config_local.example.py)
#       o thu muc goc, KHONG commit len Git.
# ============================================================
try:
    from config_local import *  # noqa: F401,F403
except ImportError:
    pass
