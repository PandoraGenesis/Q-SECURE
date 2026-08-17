"""
image_crypto.py
================
Module ma hoa/giai ma anh bang phep XOR, dung khoa nhi phan lay tu
qua trinh QKD (vd tu qkd_logic.py) lam key-stream. Doc lap voi GUI/
mang - chi lam viec voi duong dan file va mang NumPy, nen goi va kiem
thu truc tiep duoc, khong can chay ca ung dung.

Nguyen ly: XOR la phep tu nghich dao (A XOR K XOR K = A), nen dung
CHINH XAC cung mot key-stream cho ca hai chieu ma hoa/giai ma se khoi
phuc anh goc hoan hao tung byte mot - khong mat mat du lieu, khac voi
cac phep nen anh thong thuong (jpeg...).
"""
import cv2
import numpy as np


# ============================================================
# 1. CHUYEN CHUOI BIT THANH CHUOI BYTE KHOA (helper dung chung)
# ============================================================
def _normalize_bit_string(binary_key) -> str:
    """
    Chuan hoa binary_key ve dang chuoi ky tu '0'/'1'. Chap nhan ca
    chuoi co san (vd "1011...") lan list/tuple/mang cac so 0/1 (vd
    dau ra truc tiep tu qkd_logic.calculate_qber()), de khong bat
    nguoi goi phai tu chuyen doi truoc.
    """
    if isinstance(binary_key, str):
        bit_string = binary_key
    else:
        bit_string = "".join(str(int(b)) for b in binary_key)

    if not bit_string:
        raise ValueError("binary_key không được rỗng.")
    if any(c not in "01" for c in bit_string):
        raise ValueError("binary_key chỉ được chứa ký tự '0' và '1' (hoặc các giá trị 0/1).")

    return bit_string


def _bits_to_key_bytes(binary_key) -> np.ndarray:
    """
    Gom moi 8 bit trong binary_key thanh 1 byte (gia tri 0-255), tao
    thanh mang uint8. Neu do dai bit khong chia het cho 8, dem them
    so 0 vao CUOI chuoi cho du 1 byte cuoi cung - phan dem them nay
    khong lam khoa yeu di dang ke, vi no chi anh huong toi da 7 bit
    cuoi trong ca chuoi khoa von co the dai hang tram/nghin bit.
    """
    bit_string = _normalize_bit_string(binary_key)

    remainder = len(bit_string) % 8
    if remainder != 0:
        bit_string += "0" * (8 - remainder)

    byte_values = [int(bit_string[i:i + 8], 2) for i in range(0, len(bit_string), 8)]
    return np.array(byte_values, dtype=np.uint8)


def _build_key_stream(binary_key, total_bytes: int) -> np.ndarray:
    """
    Lap lai (tile/repeat) chuoi byte sinh tu binary_key cho toi khi
    du dai dung bang total_bytes - vi khoa QKD thuc te thuong NGAN
    hon nhieu so voi tong so byte cua mot buc anh (vai tram bit khoa
    so voi hang chuc nghin byte anh), nen bat buoc phai lap lai theo
    chu ky de phu kin duoc toan bo anh.
    """
    key_bytes = _bits_to_key_bytes(binary_key)
    repeats = int(np.ceil(total_bytes / key_bytes.size))
    tiled = np.tile(key_bytes, repeats)
    return tiled[:total_bytes]


# ============================================================
# 2. MA HOA ANH
# ============================================================
def encrypt_image(image_path: str, binary_key):
    """
    Doc anh tu duong dan, XOR toan bo diem anh voi key-stream lap lai
    tu binary_key, tra ve ca ma tran anh (de hien thi) lan mang byte
    phang (de gui qua TCP Socket).

    Args:
        image_path: duong dan file anh (vd "anh_goc.png").
        binary_key: chuoi khoa nhi phan (chuoi '0'/'1', hoac list/mang
            cac gia tri 0/1 - vd lay truc tiep tu ket qua sift/QBER
            cua qkd_logic.py).

    Returns:
        tuple (encrypted_matrix, encrypted_bytes, original_shape):
            encrypted_matrix: numpy.ndarray cung shape voi anh goc,
                dung de hien thi truc tiep bang cv2.imshow()/imwrite().
            encrypted_bytes: bytes phang (1 chieu), dung de gui qua
                TCP Socket - phia nhan can biet them original_shape
                de dung lai dung ma tran (vi bytes phang khong tu
                mang theo thong tin kich thuoc/so kenh mau).
            original_shape: tuple (height, width, channels) cua anh
                goc - GUI can gui kem gia tri nay sang phia Bob de
                decrypt_image() dung lai dung.

    Raises:
        FileNotFoundError: neu khong doc duoc anh tu image_path (sai
            duong dan, file hong, hoac dinh dang khong ho tro).
        ValueError: neu binary_key rong hoac chua ky tu khac '0'/'1'.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(
            f"Không đọc được ảnh tại '{image_path}' — kiểm tra lại đường dẫn hoặc định dạng file."
        )

    original_shape = image.shape  # (height, width, channels) - vd (240, 320, 3)
    flat_image = image.reshape(-1).astype(np.uint8)  # ma tran -> mang byte 1 chieu

    key_stream = _build_key_stream(binary_key, flat_image.size)

    encrypted_flat = np.bitwise_xor(flat_image, key_stream)
    encrypted_matrix = encrypted_flat.reshape(original_shape)
    encrypted_bytes = encrypted_flat.tobytes()

    return encrypted_matrix, encrypted_bytes, original_shape


# ============================================================
# 3. GIAI MA ANH
# ============================================================
def decrypt_image(encrypted_bytes: bytes, binary_key, original_shape):
    """
    XOR lai mang byte da ma hoa voi CHINH XAC cung key-stream da dung
    luc ma hoa (nho lap lai theo dung binary_key va do dai), khoi
    phuc hoan hao anh goc - khong sai lech du chi 1 byte.

    Args:
        encrypted_bytes: mang byte da ma hoa (vd nhan duoc qua TCP
            Socket) - phai la kieu bytes/bytearray hoac tuong duong.
        binary_key: BAT BUOC phai giong het chuoi khoa da dung luc
            goi encrypt_image(), neu khong ket qua giai ma se sai
            hoan toan (khong phai loi - day chinh la co che bao mat
            cot loi cua XOR: sai khoa la khong the doc duoc gi).
        original_shape: tuple (height, width, channels) cua anh goc -
            lay tu gia tri encrypt_image() da tra ve, can gui kem
            theo encrypted_bytes qua mang de dung lai dung o day.

    Returns:
        tuple (decrypted_matrix, decrypted_bytes):
            decrypted_matrix: numpy.ndarray - anh da khoi phuc, dung
                de hien thi truc tiep bang cv2.imshow()/imwrite().
            decrypted_bytes: bytes phang cua anh da khoi phuc.

    Raises:
        ValueError: neu so byte trong encrypted_bytes khong khop voi
            original_shape (du lieu bi thieu/du, hoac shape sai), hoac
            binary_key rong/chua ky tu khac '0'/'1'.
    """
    encrypted_flat = np.frombuffer(encrypted_bytes, dtype=np.uint8)

    expected_size = int(np.prod(original_shape))
    if encrypted_flat.size != expected_size:
        raise ValueError(
            f"Số byte ảnh mã hoá ({encrypted_flat.size}) không khớp với "
            f"original_shape {original_shape} (kỳ vọng {expected_size} byte). "
            f"Có thể dữ liệu bị thiếu/dư khi truyền qua mạng, hoặc original_shape sai."
        )

    key_stream = _build_key_stream(binary_key, encrypted_flat.size)

    decrypted_flat = np.bitwise_xor(encrypted_flat, key_stream)
    decrypted_matrix = decrypted_flat.reshape(original_shape)
    decrypted_bytes = decrypted_flat.tobytes()

    return decrypted_matrix, decrypted_bytes


# ============================================================
# KHOI KIEM THU DOC LAP
# ============================================================
if __name__ == "__main__":
    import os
    import tempfile

    print("=" * 60)
    print("CHUAN BI ANH MAU DE KIEM THU")
    print("=" * 60)

    # Khong co san anh mau tren dia, nen tu sinh mot anh nho co mau
    # sac/hoa tiet ro rang (khong phai anh trang tron mot mau) de de
    # nhan ra bang mat neu XOR co hieu luc hay khong.
    rng = np.random.default_rng(42)
    sample_image = rng.integers(0, 256, size=(48, 64, 3), dtype=np.uint8)

    tmp_dir = tempfile.mkdtemp()
    sample_path = os.path.join(tmp_dir, "anh_mau.png")
    cv2.imwrite(sample_path, sample_image)
    print(f"Đã tạo ảnh mẫu {sample_image.shape} tại: {sample_path}")

    # Khoa nhi phan gia lap, NGAN HON nhieu so voi anh (chi 64 bit so
    # voi anh 48x64x3 = 9216 byte) - de kiem tra dung co che lap lai
    # (tile/repeat) hoat dong dung, khong phai truong hop khoa du dai.
    fake_binary_key = "".join(str(rng.integers(0, 2)) for _ in range(64))
    print(f"Khóa nhị phân giả lập ({len(fake_binary_key)} bit): {fake_binary_key}")

    print()
    print("=" * 60)
    print("KICH BAN 1: Ma hoa roi giai ma bang DUNG khoa -> phai khop tuyet doi")
    print("=" * 60)

    enc_matrix, enc_bytes, shape = encrypt_image(sample_path, fake_binary_key)
    print(f"Đã mã hoá: shape={enc_matrix.shape}, số byte gửi qua mạng={len(enc_bytes)}")
    print(f"5 byte đầu ảnh gốc     : {sample_image.reshape(-1)[:5].tolist()}")
    print(f"5 byte đầu ảnh mã hoá  : {enc_matrix.reshape(-1)[:5].tolist()}")

    dec_matrix, dec_bytes = decrypt_image(enc_bytes, fake_binary_key, shape)
    is_pixel_perfect = np.array_equal(dec_matrix, sample_image)
    print(f"5 byte đầu ảnh giải mã : {dec_matrix.reshape(-1)[:5].tolist()}")
    print(f"Khôi phục khớp TUYỆT ĐỐI ảnh gốc: {is_pixel_perfect}")
    assert is_pixel_perfect, "LỖI: ảnh giải mã không khớp ảnh gốc dù dùng đúng khoá!"
    assert dec_bytes == sample_image.reshape(-1).tobytes(), "LỖI: chuỗi byte giải mã không khớp!"
    print("OK: giải mã bằng đúng khoá khôi phục ảnh hoàn hảo, không sai một byte nào.")

    print()
    print("=" * 60)
    print("KICH BAN 2: Giai ma bang SAI khoa -> anh phai vo vun, KHONG duoc khop")
    print("=" * 60)

    wrong_key = "".join(str(rng.integers(0, 2)) for _ in range(64))
    wrong_matrix, _ = decrypt_image(enc_bytes, wrong_key, shape)
    is_wrong_match = np.array_equal(wrong_matrix, sample_image)
    diff_ratio = np.mean(wrong_matrix != sample_image) * 100
    print(f"Khoá sai có vô tình khớp ảnh gốc không: {is_wrong_match}")
    print(f"Tỷ lệ byte sai lệch so với ảnh gốc: {diff_ratio:.1f}%")
    assert not is_wrong_match, "LỖI: khoá sai lại vô tình giải mã đúng — không hợp lý!"
    print("OK: dùng sai khoá thì ảnh giải mã hoàn toàn không khớp, đúng nguyên lý bảo mật của XOR.")

    print()
    print("=" * 60)
    print("KICH BAN 3: Kiem tra loi dau vao duoc bat dung")
    print("=" * 60)

    try:
        encrypt_image("duong_dan_khong_ton_tai.png", fake_binary_key)
        print("SAI: lẽ ra phải raise FileNotFoundError")
    except FileNotFoundError as e:
        print(f"OK: bắt đúng lỗi file không tồn tại -> {e}")

    try:
        decrypt_image(enc_bytes, fake_binary_key, (10, 10, 3))  # shape sai co tinh
        print("SAI: lẽ ra phải raise ValueError")
    except ValueError as e:
        print(f"OK: bắt đúng lỗi shape không khớp -> {e}")

    try:
        encrypt_image(sample_path, "khong-phai-bit")
        print("SAI: lẽ ra phải raise ValueError")
    except ValueError as e:
        print(f"OK: bắt đúng lỗi binary_key không hợp lệ -> {e}")

    print()
    print("TẤT CẢ KỊCH BẢN KIỂM THỬ ĐỀU PASS.")
