"""
main.py — Diem khoi chay chinh cua Q-SECURE.

Doc ROLE tu config (ALICE hoac BOB) roi khoi tao dung giao dien +
worker tuong ung. Day la file DUY NHAT khac nhau ve luong chay giua
2 may, nhung ban than file nay khong chua logic nghiep vu.
"""
import sys
from PyQt6.QtWidgets import QApplication

from config import DEVICE_ROLE, Role
from src.gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    window = MainWindow(role=DEVICE_ROLE)
    window.setWindowTitle(f"Q-SECURE - {DEVICE_ROLE.value}")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
