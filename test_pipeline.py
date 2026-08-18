"""
test_pipeline.py
=================
Kich ban kiem thu TICH HOP TOAN BO pipeline phan mem cua du an
Hermex, chay tren dong lenh (CLI) - khong can giao dien PyQt6,
khong can phan cung ESP32 that. Xac nhan cac module da xay dung rieng
le (qkd_logic.py, image_crypto.py) cung tang mang TCP Socket phoi hop
DUNG voi nhau thanh mot pipeline hoan chinh: sinh bit/basis -> sifting
-> tinh QBER -> ma hoa anh -> truyen qua TCP that -> giai ma -> doi
chieu voi anh goc.

Chay:
    python test_pipeline.py

Ma thoat: 0 neu TOAN BO buoc PASSED, 1 neu co it nhat 1 buoc FAILED -
tien loi de dung trong CI hoac script khac kiem tra qua bien $?.
"""
import os
import random
import socket
import struct
import sys
import threading
import time

import cv2
import numpy as np

from image_crypto import decrypt_image, encrypt_image
from qkd_logic import calculate_qber, sift_keys

TEST_IMAGE_PATH = "test.png"
TCP_HOST = "127.0.0.1"
TCP_PORT = 5091
QBER_THRESHOLD_PERCENT = 11.0
NUM_RAW_BITS = 512  # khop QKD_PARAMS["KEY_LENGTH_RAW"] trong config.py cua du an


# ============================================================
# TIEN ICH IN BAO CAO TUNG BUOC (Status: PASSED / FAILED)
# ============================================================
class StepReport:
    def __init__(self):
        self.steps = []  # list[(ten_buoc, da_pass, [chi_tiet...])]

    def add(self, name: str, passed: bool, details=None):
        self.steps.append((name, passed, details or []))

    def print_report(self) -> bool:
        print("=" * 70)
        print("  Hermex — KIỂM THỬ TÍCH HỢP TOÀN BỘ PIPELINE")
        print("=" * 70)
        print()

        total = len(self.steps)
        for i, (name, passed, details) in enumerate(self.steps, start=1):
            status = "PASSED" if passed else "FAILED"
            marker = "✓" if passed else "✗"
            print(f"[Bước {i}/{total}] {name}")
            for d in details:
                print(f"    - {d}")
            print(f"    => Status: {status} {marker}")
            print()

        passed_count = sum(1 for _, p, _ in self.steps if p)
        print("=" * 70)
        if passed_count == total:
            print(f"  KẾT QUẢ: {passed_count}/{total} bước PASSED — TOÀN BỘ PIPELINE HOẠT ĐỘNG ĐÚNG")
        else:
            print(f"  KẾT QUẢ: {passed_count}/{total} bước PASSED — CÓ {total - passed_count} BƯỚC THẤT BẠI")
        print("=" * 70)
        return passed_count == total


report = StepReport()


# ============================================================
# MO PHONG VAT LY: (basis, bit) <-> goc, va phep do luong tu - dung
# chung logic da dung xuyen suot du an (trang web mo phong, hermex_app.py).
# ============================================================
def measure(sent_basis, sent_bit, measure_basis):
    """Do dung basis -> luon ra dung bit da gui; do sai basis -> ngau nhien 50/50."""
    if sent_basis == measure_basis:
        return sent_bit
    return random.randint(0, 1)


def ensure_test_image(path: str = TEST_IMAGE_PATH) -> None:
    """Neu chua co san test.png, tu sinh 1 anh mau de kich ban chay duoc ngay ma khong can chuan bi truoc."""
    if os.path.exists(path):
        return
    rng = np.random.default_rng(2026)
    sample = rng.integers(0, 256, size=(64, 64, 3), dtype=np.uint8)
    cv2.imwrite(path, sample)


def recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("kết nối bị đóng giữa chừng khi đang nhận dữ liệu")
        buf.extend(chunk)
    return bytes(buf)


# ============================================================
# BƯỚC 1: GIẢ LẬP CHUỖI BIT VÀ GÓC ĐO CỦA ALICE & BOB
# ============================================================
def step1_simulate():
    try:
        alice_bits = [random.randint(0, 1) for _ in range(NUM_RAW_BITS)]
        alice_bases = [random.choice(["+", "x"]) for _ in range(NUM_RAW_BITS)]
        bob_bases = [random.choice(["+", "x"]) for _ in range(NUM_RAW_BITS)]
        bob_bits = [measure(alice_bases[i], alice_bits[i], bob_bases[i]) for i in range(NUM_RAW_BITS)]

        report.add(
            "Giả lập chuỗi bit và góc đo (basis) của Alice & Bob",
            True,
            [
                f"Số bit thô: {NUM_RAW_BITS}",
                f"5 bit đầu của Alice : {alice_bits[:5]}",
                f"5 basis đầu Alice   : {alice_bases[:5]}",
                f"5 basis đầu Bob     : {bob_bases[:5]}",
            ],
        )
        return alice_bits, alice_bases, bob_bits, bob_bases
    except Exception as e:
        report.add("Giả lập chuỗi bit và góc đo (basis) của Alice & Bob", False, [f"Lỗi: {e}"])
        raise


# ============================================================
# BƯỚC 2: THỰC THI SIFTING (qkd_logic.sift_keys) ĐỂ TẠO KHOÁ
# ============================================================
def step2_sifting(alice_bits, alice_bases, bob_bits, bob_bases):
    try:
        alice_sifted, bob_sifted, matched = sift_keys(alice_bases, bob_bases, alice_bits, bob_bits)
        keep_ratio = len(matched) / NUM_RAW_BITS * 100

        assert len(alice_sifted) == len(bob_sifted) == len(matched), \
            "độ dài khoá thô 2 bên và danh sách vị trí trùng khớp không nhất quán"
        # Ve mat ly thuyet, ty le giu lai phai quanh 50% (2 basis doc lap ngau nhien) -
        # kiem tra ranh gioi rong (30-70%) de bat loi logic ro rang ma khong qua nhay cam
        # voi dao dong ngau nhien thong thuong cua 1 lan chay.
        assert 30 <= keep_ratio <= 70, \
            f"tỷ lệ giữ lại sau sifting bất thường ({keep_ratio:.1f}%, kỳ vọng quanh 50%)"

        report.add(
            "Thực thi Sifting (qkd_logic.sift_keys) để tạo Khoá",
            True,
            [f"Số bit giữ lại sau sifting: {len(matched)}/{NUM_RAW_BITS} ({keep_ratio:.1f}%, kỳ vọng ~50%)"],
        )
        return alice_sifted, bob_sifted
    except Exception as e:
        report.add("Thực thi Sifting (qkd_logic.sift_keys) để tạo Khoá", False, [f"Lỗi: {e}"])
        raise


# ============================================================
# BƯỚC 3: TÍNH QBER, NẾU ≤ 11% THÌ MÃ HOÁ test.png
# ============================================================
def step3_qber_and_encrypt(alice_sifted, bob_sifted):
    try:
        qber_percent, final_key = calculate_qber(alice_sifted, bob_sifted, sample_ratio=0.2)
        is_safe = qber_percent <= QBER_THRESHOLD_PERCENT

        details = [
            f"QBER đo được       : {qber_percent:.2f}%",
            f"Ngưỡng an toàn      : {QBER_THRESHOLD_PERCENT}%",
            f"Khoá cuối cùng còn  : {len(final_key)} bit",
        ]

        if not is_safe:
            details.append("QBER VƯỢT NGƯỠNG — huỷ phiên, KHÔNG mã hoá ảnh (đúng thiết kế bảo mật của BB84).")
            report.add("Tính QBER, mã hoá ảnh test.png (qkd_logic + image_crypto)", False, details)
            raise RuntimeError(f"QBER {qber_percent:.2f}% vượt ngưỡng an toàn {QBER_THRESHOLD_PERCENT}%")

        if not final_key:
            details.append("Khoá cuối cùng rỗng sau khi lấy mẫu — không đủ dữ liệu để mã hoá.")
            report.add("Tính QBER, mã hoá ảnh test.png (qkd_logic + image_crypto)", False, details)
            raise RuntimeError("Khoá cuối cùng rỗng, không thể mã hoá ảnh")

        ensure_test_image(TEST_IMAGE_PATH)
        enc_matrix, enc_bytes, shape = encrypt_image(TEST_IMAGE_PATH, final_key)
        details.append(f"Đã mã hoá '{TEST_IMAGE_PATH}' — shape={shape}, {len(enc_bytes)} byte")

        report.add("Tính QBER, mã hoá ảnh test.png (qkd_logic + image_crypto)", True, details)
        return final_key, enc_bytes, shape
    except RuntimeError:
        raise
    except Exception as e:
        report.add("Tính QBER, mã hoá ảnh test.png (qkd_logic + image_crypto)", False, [f"Lỗi: {e}"])
        raise


# ============================================================
# BƯỚC 4: GIẢ LẬP GỬI MẢNG BYTE ẢNH MÃ HOÁ QUA TCP SOCKET NỘI BỘ
# Khung du lieu: 4 byte do dai (big-endian) + payload nhi phan. Chay
# 1 server that (dong vai Bob, lang nghe tren 127.0.0.1) tren luong
# rieng, song song voi luong chinh dong vai Alice (client, ket noi
# va gui) - giao tiep qua SOCKET TCP THAT, khong phai truyen bien
# trong bo nho.
# ============================================================
def step4_send_over_tcp(enc_bytes: bytes) -> bytes:
    received_holder = {}
    server_error = {}

    def bob_server_thread():
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((TCP_HOST, TCP_PORT))
            srv.listen(1)
            conn, _addr = srv.accept()

            header = recv_exact(conn, 4)
            (length,) = struct.unpack(">I", header)
            received_holder["bytes"] = recv_exact(conn, length)

            conn.close()
            srv.close()
        except Exception as e:  # noqa: BLE001 - can bat rong de bao loi ro thay vi lam thread chet am tham
            server_error["error"] = str(e)

    try:
        server_thread = threading.Thread(target=bob_server_thread, daemon=True)
        server_thread.start()
        time.sleep(0.3)  # cho server vao trang thai listen() truoc khi client ket noi

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5)
        client.connect((TCP_HOST, TCP_PORT))
        client.sendall(struct.pack(">I", len(enc_bytes)) + enc_bytes)
        client.close()

        server_thread.join(timeout=5)

        if server_error:
            raise RuntimeError(f"lỗi phía nhận (Bob): {server_error['error']}")
        if "bytes" not in received_holder:
            raise RuntimeError("không nhận được dữ liệu nào trong thời gian chờ cho phép")

        received = received_holder["bytes"]
        if received != enc_bytes:
            raise RuntimeError("dữ liệu nhận được KHÔNG khớp dữ liệu đã gửi (bị hỏng khi truyền)")

        report.add(
            "Giả lập gửi ảnh mã hoá qua TCP Socket nội bộ (127.0.0.1)",
            True,
            [
                f"Địa chỉ: {TCP_HOST}:{TCP_PORT}",
                f"Đã gửi và nhận đúng {len(received)} byte, khớp tuyệt đối dữ liệu gốc",
            ],
        )
        return received
    except Exception as e:
        report.add("Giả lập gửi ảnh mã hoá qua TCP Socket nội bộ (127.0.0.1)", False, [f"Lỗi: {e}"])
        raise


# ============================================================
# BƯỚC 5: GIẢI MÃ ẢNH Ở PHÍA BOB, SO KHỚP 100% VỚI ẢNH GỐC
# ============================================================
def step5_decrypt_and_verify(received_bytes: bytes, final_key, shape) -> None:
    try:
        dec_matrix, _dec_bytes = decrypt_image(received_bytes, final_key, shape)
        original = cv2.imread(TEST_IMAGE_PATH)

        pixel_perfect = bool(np.array_equal(dec_matrix, original))
        details = [
            f"Ảnh gốc: {original.shape}  |  Ảnh giải mã: {dec_matrix.shape}",
            f"Khớp tuyệt đối 100% với ảnh gốc: {pixel_perfect}",
        ]
        if not pixel_perfect:
            diff_ratio = float(np.mean(dec_matrix != original) * 100)
            details.append(f"Tỷ lệ byte sai lệch so với ảnh gốc: {diff_ratio:.2f}%")

        report.add("Giải mã ảnh phía Bob, kiểm tra khớp 100% ảnh gốc", pixel_perfect, details)

        if not pixel_perfect:
            raise RuntimeError("ảnh giải mã KHÔNG khớp tuyệt đối ảnh gốc")
    except RuntimeError:
        raise
    except Exception as e:
        report.add("Giải mã ảnh phía Bob, kiểm tra khớp 100% ảnh gốc", False, [f"Lỗi: {e}"])
        raise


# ============================================================
# BONUS (khong tinh vao 5 buoc chinh thuc): kiem tra co che phat
# hien nghe len van hoat dong dung - mo phong Eve gay nhieu ~25%,
# xac nhan QBER vuot nguong va pipeline se HUY dung nhu thiet ke.
# ============================================================
def bonus_eve_detection_check():
    print("-" * 70)
    print("  BONUS: kiểm tra cơ chế phát hiện nghe lén (không tính vào 5 bước chính)")
    print("-" * 70)

    alice_bits = [random.randint(0, 1) for _ in range(NUM_RAW_BITS)]
    alice_bases = [random.choice(["+", "x"]) for _ in range(NUM_RAW_BITS)]
    bob_bases = [random.choice(["+", "x"]) for _ in range(NUM_RAW_BITS)]

    def noisy_measure(sent_basis, sent_bit, measure_basis):
        result = measure(sent_basis, sent_bit, measure_basis)
        if sent_basis == measure_basis and random.random() < 0.25:
            result = 1 - result  # mo phong hau qua cua Eve chen giua duong truyen
        return result

    bob_bits = [noisy_measure(alice_bases[i], alice_bits[i], bob_bases[i]) for i in range(NUM_RAW_BITS)]
    alice_sifted, bob_sifted, _ = sift_keys(alice_bases, bob_bases, alice_bits, bob_bits)
    qber_percent, _ = calculate_qber(alice_sifted, bob_sifted, sample_ratio=0.2)

    detected = qber_percent > QBER_THRESHOLD_PERCENT
    print(f"    - QBER đo được khi có Eve mô phỏng: {qber_percent:.2f}% (ngưỡng {QBER_THRESHOLD_PERCENT}%)")
    print(f"    - Phát hiện đúng nghi vấn nghe lén : {detected}")
    print(f"    => Status: {'PASSED' if detected else 'FAILED'} {'✓' if detected else '✗'}")
    print()
    return detected


# ============================================================
# HÀM CHÍNH
# ============================================================
def main():
    try:
        alice_bits, alice_bases, bob_bits, bob_bases = step1_simulate()
        alice_sifted, bob_sifted = step2_sifting(alice_bits, alice_bases, bob_bits, bob_bases)
        final_key, enc_bytes, shape = step3_qber_and_encrypt(alice_sifted, bob_sifted)
        received_bytes = step4_send_over_tcp(enc_bytes)
        step5_decrypt_and_verify(received_bytes, final_key, shape)
    except Exception:
        pass  # da ghi nhan chi tiet loi vao report ngay tai buoc that bai, khong can xu ly them o day

    all_passed = report.print_report()
    print()
    bonus_eve_detection_check()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
