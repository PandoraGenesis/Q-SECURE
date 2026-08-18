"""
logger.py — Cau hinh logging dung chung cho toan bo ung dung
(ghi ra console + file trong thu muc logs/).
"""
import logging
import os

from config import PATHS


def get_logger(name: str) -> logging.Logger:
    os.makedirs(PATHS["LOG_DIR"], exist_ok=True)
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        file_handler = logging.FileHandler(
            os.path.join(PATHS["LOG_DIR"], "hermex.log"), encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
