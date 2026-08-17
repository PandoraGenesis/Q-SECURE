"""
bb84_protocol.py — Sinh chuoi bit/basis ngau nhien mo phong BB84
va cac ham dung chung cho ca Alice & Bob (khong phu thuoc GUI/mang).
"""
import numpy as np


def generate_random_bits(n: int) -> np.ndarray:
    """Sinh n bit ngau nhien (0/1)."""
    raise NotImplementedError


def generate_random_bases(n: int) -> np.ndarray:
    """Sinh n basis ngau nhien (vd 0 = +, 1 = x)."""
    raise NotImplementedError


def measure_qubits(bits: np.ndarray, bases_sender, bases_receiver) -> np.ndarray:
    """Mo phong ket qua do khi basis nguoi gui/nhan khac hoac giong nhau."""
    raise NotImplementedError
