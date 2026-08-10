"""
main_window.py — QMainWindow trung tam. Dua vao role (ALICE/BOB)
de nhung dung view (AliceView hoac BobView) vao trong.
"""
from PyQt6.QtWidgets import QMainWindow

from config import Role
from src.gui.alice_view import AliceView
from src.gui.bob_view import BobView


class MainWindow(QMainWindow):
    def __init__(self, role: Role):
        super().__init__()
        self.role = role

        if role == Role.ALICE:
            self.setCentralWidget(AliceView(self))
        else:
            self.setCentralWidget(BobView(self))
