"""
ldr_calibration.py
===================
Module hieu chuan anh sang moi truong cho cam bien LDR, chay TRUOC khi
demo QKD that. Muc dich: xac dinh nguong phan biet bit 0/1 phu hop voi
DUNG dieu kien anh sang cua can phong luc do (thay vi dung mot con so
co dinh trong code, se sai lech neu demo o phong sang hon/toi hon so
voi luc code duoc viet).

Khong phu thuoc vao esp32_serial.SerialManager hay bat ky module nao
khac cua du an - chi can mot doi tuong "giong Serial" (co phuong thuc
readline() tra ve bytes, vd serial.Serial(...) chuan cua pyserial),
nen goi va kiem thu doc lap duoc.
"""
import json
import os
import statistics
import time
from datetime import datetime

DEFAULT_CONFIG_PATH = "config.json"
DEFAULT_SAFETY_OFFSET = 300  # gia tri ADC (thang 0-4095, ADC 12-bit tren ESP32-C3)


# ============================================================
# 1. DOC 1 MAU LDR HOP LE TU SERIAL (bo qua dong rac/log khac)
# ============================================================
def _read_one_ldr_sample(serial_conn, read_timeout_s: float = 3.0) -> int:
    """
    Doc tung dong tu serial_conn cho toi khi gap dung dinh dang
    "LDR:<so_nguyen>" thi tra ve gia tri do - cac dong khac (log debug,
    ACK, du lieu nhieu tin hieu...) deu bi bo qua thay vi lam crash.
    """
    deadline = time.monotonic() + read_timeout_s
    while time.monotonic() < deadline:
        raw = serial_conn.readline()
        if not raw:
            continue  # het timeout doc rieng cua serial_conn, chua chac da het read_timeout_s tong the

        try:
            line = raw.decode("utf-8", errors="strict").strip()
        except UnicodeDecodeError:
            continue  # du lieu nhieu tin hieu o tang byte, bo qua dong nay

        if not line.startswith("LDR:"):
            continue  # dong khac (log, ACK...) - khong phai loi, chi bo qua

        try:
            return int(line[len("LDR:"):])
        except ValueError:
            continue  # dung tien to nhung phan gia tri hong (nhieu o tang noi dung)

    raise TimeoutError(
        f"Không nhận được dòng 'LDR:<giá trị>' hợp lệ nào trong {read_timeout_s}s. "
        f"Kiểm tra: ESP32 đã cắm đúng cổng, đúng baudrate, và đang chạy firmware "
        f"có gửi dữ liệu LDR chưa."
    )


# ============================================================
# 2. HIEU CHUAN: DOC N MAU, TINH MEAN + STDEV
# ============================================================
def calibrate_ambient_light(serial_conn, samples: int = 20, delay_ms: int = 100) -> dict:
    """
    Doc lien tiep `samples` gia tri LDR tu MOI TRUONG (chua bat den/
    laser tin hieu), tinh gia tri trung binh (mean) va do lech chuan
    (standard deviation) cua anh sang nen.

    Args:
        serial_conn: doi tuong da MO SAN ket noi Serial, co phuong thuc
            readline() tra ve bytes - vd serial.Serial(port, baudrate,
            timeout=...) chuan cua pyserial.
        samples: so mau can doc (mac dinh 20).
        delay_ms: khoang cho giua 2 lan doc lien tiep, tinh bang mili-
            giay (mac dinh 100ms) - tranh doc don ADC lien tuc qua
            nhanh khien gia tri bi nhieu do chinh no lay mau qua sat nhau.

    Returns:
        dict {
            "mean": float,   # trung binh anh sang moi truong
            "stdev": float,  # do lech chuan (mau, n-1) - do bien thien tu nhien
            "samples": list[int],  # toan bo gia tri tho da doc, de debug/ve bieu do
            "n": int,        # so mau thuc te da dung
        }

    Raises:
        ValueError: neu samples < 2 (khong du du lieu de tinh do lech chuan).
        TimeoutError: neu khong doc duoc du so mau hop le trong thoi gian cho phep.
    """
    if samples < 2:
        raise ValueError("samples phải >= 2 để tính được độ lệch chuẩn (standard deviation).")

    readings = []
    for i in range(samples):
        value = _read_one_ldr_sample(serial_conn)
        readings.append(value)
        if i < samples - 1:
            time.sleep(delay_ms / 1000)

    return {
        "mean": statistics.mean(readings),
        "stdev": statistics.stdev(readings),  # do lech chuan MAU (chia n-1), dung khi day la 1 mau chu khong phai toan bo tong the
        "samples": readings,
        "n": samples,
    }


# ============================================================
# 3. TINH NGUONG DONG (DYNAMIC THRESHOLD)
# ============================================================
def compute_dynamic_threshold(calibration_result: dict, safety_offset: int = DEFAULT_SAFETY_OFFSET) -> int:
    """
    Nguong phan biet bit 0/1 = trung binh anh sang moi truong + offset an toan.

    Ghi chu ve cach chon safety_offset: offset can DU LON de vuot qua
    nhieu tu nhien cua anh sang phong (do do lech chuan gay ra) nhung
    khong qua lon toi muc lam mat kha nang phan biet khi co tin hieu
    that. Mot cach chon co co so thong ke: safety_offset >= 3-5 lan
    calibration_result["stdev"] - neu do lech chuan do duoc qua lon (vd
    phong co anh sang nhap nhay/khong on dinh), gia tri offset mac dinh
    (300) co the khong du, nen kiem tra lai ty le nay truoc khi dung.
    """
    return round(calibration_result["mean"] + safety_offset)


# ============================================================
# 4. LUU NGUONG VAO config.json (khong ghi de cac khoa khac da co)
# ============================================================
def save_threshold_to_config(
    threshold: int,
    calibration_result: dict,
    config_path: str = DEFAULT_CONFIG_PATH,
) -> None:
    """
    Luu nguong vua tinh (kem thong tin hieu chuan de tra cuu/debug sau
    nay) vao file JSON, de cac module khac (vd logic doc bit trong
    demo that) tu doc lai ma khong can hieu chuan lai tu dau moi lan
    chay chuong trinh.

    Neu config_path DA TON TAI va co du lieu khac (vd cau hinh khac cua
    du an dung chung file), CHI cap nhat/them dung khoa "ldr_calibration"
    - khong lam mat cac khoa khac da co san trong file.
    """
    existing_data = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            # File hong/khong doc duoc - ghi de bang du lieu moi thay vi crash,
            # nhung KHONG am tham mat du lieu that: se in canh bao ra ngoai.
            print(f"[Cảnh báo] Không đọc được '{config_path}' hiện có (hỏng/sai định dạng) — sẽ tạo mới.")
            existing_data = {}

    existing_data["ldr_calibration"] = {
        "threshold": threshold,
        "ambient_mean": calibration_result["mean"],
        "ambient_stdev": calibration_result["stdev"],
        "n_samples": calibration_result["n"],
        "calibrated_at": datetime.now().isoformat(timespec="seconds"),
    }

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)


# ============================================================
# 5. HAM GOP GON CA 3 BUOC (dung nhanh trong script chinh)
# ============================================================
def run_calibration(
    serial_conn,
    samples: int = 20,
    delay_ms: int = 100,
    safety_offset: int = DEFAULT_SAFETY_OFFSET,
    config_path: str = DEFAULT_CONFIG_PATH,
):
    """Goi gon 3 buoc: hieu chuan -> tinh nguong -> luu file. Tra ve (threshold, calibration_result)."""
    result = calibrate_ambient_light(serial_conn, samples=samples, delay_ms=delay_ms)
    threshold = compute_dynamic_threshold(result, safety_offset=safety_offset)
    save_threshold_to_config(threshold, result, config_path=config_path)
    return threshold, result


# ============================================================
# KHOI KIEM THU DOC LAP - dung mot Serial GIA LAP (khong can phan
# cung that) de minh hoa va tu kiem tra module nay chay dung.
# ============================================================
if __name__ == "__main__":
    import random

    class _FakeAmbientSerial:
        """
        Serial gia lap, sinh du lieu "LDR:<so>" giong nhu anh sang moi
        truong that (dao dong nhe quanh 1 gia tri trung binh), kem theo
        thinh thoang chen 1 dong rac (log/ACK) de kiem tra co che bo
        qua dong khong hop le co hoat dong dung khong.
        """

        def __init__(self, mean=820, stdev=15, seed=42):
            self._rng = random.Random(seed)
            self._mean = mean
            self._stdev = stdev
            self._call_count = 0

        def readline(self) -> bytes:
            self._call_count += 1
            # Cu moi 5 lan doc thi chen 1 dong rac, mo phong log/ACK xen giua du lieu that.
            if self._call_count % 5 == 0:
                return b"ACK:SERVO:90\n"
            value = max(0, min(4095, round(self._rng.gauss(self._mean, self._stdev))))
            return f"LDR:{value}\n".encode("utf-8")

    print("=" * 60)
    print("KỊCH BẢN 1: Hiệu chuẩn với Serial giả lập (phòng ánh sáng ổn định)")
    print("=" * 60)

    fake_serial = _FakeAmbientSerial(mean=820, stdev=15)
    result = calibrate_ambient_light(fake_serial, samples=20, delay_ms=10)
    print(f"Số mẫu đã đọc     : {result['n']}")
    print(f"20 mẫu thô        : {result['samples']}")
    print(f"Trung bình (mean) : {result['mean']:.2f}")
    print(f"Độ lệch chuẩn     : {result['stdev']:.2f}")

    threshold = compute_dynamic_threshold(result, safety_offset=DEFAULT_SAFETY_OFFSET)
    print(f"Ngưỡng động (mean + offset {DEFAULT_SAFETY_OFFSET}): {threshold}")

    test_config_path = "config_demo.json"
    save_threshold_to_config(threshold, result, config_path=test_config_path)
    print(f"Đã lưu vào '{test_config_path}'. Nội dung:")
    with open(test_config_path, encoding="utf-8") as f:
        print(f.read())

    print()
    print("=" * 60)
    print("KỊCH BẢN 2: config.json đã có sẵn dữ liệu khác — không được ghi đè mất")
    print("=" * 60)

    with open(test_config_path, "w", encoding="utf-8") as f:
        json.dump({"some_other_setting": "giữ nguyên giá trị này"}, f, ensure_ascii=False, indent=2)

    threshold2, result2 = run_calibration(
        _FakeAmbientSerial(mean=700, stdev=10), samples=15, delay_ms=5, config_path=test_config_path
    )
    with open(test_config_path, encoding="utf-8") as f:
        final_data = json.load(f)
    print(json.dumps(final_data, ensure_ascii=False, indent=2))
    assert final_data.get("some_other_setting") == "giữ nguyên giá trị này", \
        "LỖI: mất dữ liệu cấu hình khác đã có sẵn trong file!"
    assert "ldr_calibration" in final_data, "LỖI: không thấy khoá ldr_calibration mới!"
    print("OK: khoá 'some_other_setting' có sẵn vẫn được giữ nguyên, chỉ thêm khoá 'ldr_calibration' mới.")

    os.remove(test_config_path)
