"""
image_cipher.py — Ma hoa / giai ma anh bang phep XOR, dung chung
khoa lugng tu da sift lam key-stream. Dung NumPy + OpenCV.
"""
import cv2
import numpy as np


def load_image(path: str) -> np.ndarray:
    return cv2.imread(path)


def xor_encrypt(image: np.ndarray, key_bits: np.ndarray) -> np.ndarray:
    """Ma hoa ma tran anh bang XOR voi key duoc mo rong (key stream)."""
    raise NotImplementedError


def xor_decrypt(cipher_image: np.ndarray, key_bits: np.ndarray) -> np.ndarray:
    """Giai ma - XOR la phep doi xung nen co the goi lai ham encrypt."""
    return xor_encrypt(cipher_image, key_bits)
