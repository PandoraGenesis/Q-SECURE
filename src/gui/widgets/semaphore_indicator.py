"""
semaphore_indicator.py — Widget hien thi anh (hoac GIF dong) "chu linh
Semaphore" tuong ung voi goc dang duoc gui/nhan (0/45/90/135 do), dung
lam minh hoa truc quan cho basis dang duoc su dung tai thoi diem do.

Ho tro ca anh tinh (.png/.jpg) lan GIF dong (.gif) - PyQt6 can 2 co che
khac nhau cho 2 loai file nay (QPixmap cho anh tinh, QMovie cho GIF
dong), nen widget tu kiem tra duoi file de chon dung co che.
"""
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMovie, QPixmap
from PyQt6.QtWidgets import QLabel

from config import PATHS


class SemaphoreIndicator(QLabel):
    """QLabel mo rong: goi set_angle(goc) de doi hinh hien thi tuong ung."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(160, 160)
        self.setStyleSheet("border: 1px solid #888;")

        # Giu tham chieu QMovie o day de GIF khong bi garbage-collected
        # giua chung (neu khong giu lai, GIF se dung hoat hinh dot ngot).
        self._movie: Optional[QMovie] = None

        self.set_angle(0)  # trang thai mac dinh khi widget vua tao

    def set_angle(self, angle: int) -> None:
        """
        Doi hinh dang hien thi sang goc `angle`. Neu khong tim thay
        file cau hinh cho goc do trong PATHS["SEMAPHORE_ICONS"], hien
        chu bao loi thay vi crash - huu ich khi ban chua tai du 4 anh.
        """
        icon_path = PATHS["SEMAPHORE_ICONS"].get(angle)

        if icon_path is None:
            self._stop_movie_if_any()
            self.setText(f"Chưa có ảnh cho góc {angle}°")
            return

        if icon_path.lower().endswith(".gif"):
            self._show_gif(icon_path)
        else:
            self._show_static_image(icon_path)

    def _show_static_image(self, path: str) -> None:
        self._stop_movie_if_any()

        pixmap = QPixmap(path)
        if pixmap.isNull():
            # File khong ton tai hoac khong doc duoc - thuong gap khi
            # ban chua tai anh ve dung duong dan trong config.py.
            self.setText(f"Không đọc được ảnh:\n{path}")
            return

        self.setPixmap(
            pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _show_gif(self, path: str) -> None:
        self._stop_movie_if_any()

        movie = QMovie(path)
        if not movie.isValid():
            self.setText(f"Không đọc được GIF:\n{path}")
            return

        movie.setScaledSize(self.size())
        self._movie = movie
        self.setMovie(self._movie)
        self._movie.start()

    def _stop_movie_if_any(self) -> None:
        """Dung GIF dang phat (neu co) truoc khi chuyen sang hinh khac,
        tranh truong hop 2 GIF chong len nhau ve mat bo nho/hien thi."""
        if self._movie is not None:
            self._movie.stop()
            self._movie = None
