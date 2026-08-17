"""
qber.py — Tinh Quantum Bit Error Rate (QBER) tu mot mau khoa
duoc cong khai so sanh giua Alice va Bob.
"""


def calculate_qber(sample_alice, sample_bob) -> float:
    """Tra ve ty le loi (0.0 - 1.0) giua 2 mau bit."""
    raise NotImplementedError


def is_channel_secure(qber: float, threshold: float) -> bool:
    """So sanh QBER voi nguong an toan (mac dinh ~11% theo chuan BB84)."""
    return qber <= threshold
