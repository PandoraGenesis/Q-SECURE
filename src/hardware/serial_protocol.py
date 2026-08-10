"""
serial_protocol.py — Dinh nghia khung lenh trao doi voi ESP32
qua Serial (vd: lenh yeu cau sinh photon/basis, lenh doc trang thai...).

Quy uoc de xuat: moi dong ket thuc bang '\n', dang text don gian
"CMD:<ten_lenh>;<tham_so_1>,<tham_so_2>...".
"""

CMD_REQUEST_BITS = "REQUEST_BITS"
CMD_SET_BASIS = "SET_BASIS"
CMD_ACK = "ACK"


def build_command(cmd: str, *args) -> bytes:
    payload = f"CMD:{cmd};" + ",".join(str(a) for a in args) + "\n"
    return payload.encode("utf-8")


def parse_response(line: bytes) -> dict:
    """Phan tich 1 dong phan hoi tu ESP32 thanh dict {cmd, args}."""
    raise NotImplementedError
