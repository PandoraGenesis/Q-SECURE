"""
qkd_logic.py
============
Module xu ly logic cot loi cua giao thuc BB84 cho du an Q-SECURE:
loc khoa (sifting) va tinh ty le loi bit luong tu (QBER).

Module nay khong phu thuoc gi vao GUI, mang, hay phan cung - chi lam
viec voi cac mang bit/basis thuan Python (list), nen co the goi truc
tiep va kiem thu doc lap, khong can chay ca ung dung.
"""
import random


# ============================================================
# 1. SIFTING - LOC KHOA THEO BASIS TRUNG KHOP
# ============================================================
def sift_keys(alice_bases, bob_bases, alice_bits, bob_bits):
    """
    So sanh mang basis (co so/goc do) giua Alice va Bob theo tung vi
    tri. Chi giu lai bit tai nhung vi tri ca hai ben TINH CO chon
    trung basis - day chinh la buoc sifting trong BB84, loai bo hoan
    toan nhung vi tri lech basis vi ket qua do o do khong dang tin
    cay (mang tinh ngau nhien, khong phan anh dung bit da gui).

    Args:
        alice_bases: danh sach basis Alice da dung de chuan bi tung bit
            (vd list ky tu '+'/'x', hoac list so 0/1 - chi can cung
            kieu du lieu so sanh duoc bang '==').
        bob_bases: danh sach basis Bob da dung de do tung bit, cung
            do dai voi alice_bases.
        alice_bits: danh sach bit goc Alice da gui, cung do dai.
        bob_bits: danh sach bit Bob do duoc, cung do dai.

    Returns:
        tuple (alice_sifted, bob_sifted, matched_indices):
            alice_sifted: list bit cua Alice tai cac vi tri basis trung.
            bob_sifted: list bit cua Bob tai cung cac vi tri do.
            matched_indices: list vi tri (index) basis trung khop.
        Tra ve rieng ca hai ben (khong gop chung thanh 1 mang) vi day
        la 2 "ban sao" khoa tho doc lap - chenh lech giua chung (neu
        co) chinh la thu ma calculate_qber() ben duoi do luong.

    Raises:
        ValueError: neu 4 mang dau vao khong cung do dai.
    """
    lengths = {len(alice_bases), len(bob_bases), len(alice_bits), len(bob_bits)}
    if len(lengths) != 1:
        raise ValueError(
            f"Ca 4 mang dau vao phai cung do dai, hien tai: "
            f"alice_bases={len(alice_bases)}, bob_bases={len(bob_bases)}, "
            f"alice_bits={len(alice_bits)}, bob_bits={len(bob_bits)}"
        )

    alice_sifted = []
    bob_sifted = []
    matched_indices = []

    for i in range(len(alice_bases)):
        if alice_bases[i] == bob_bases[i]:
            alice_sifted.append(alice_bits[i])
            bob_sifted.append(bob_bits[i])
            matched_indices.append(i)

    return alice_sifted, bob_sifted, matched_indices


# ============================================================
# 2. TINH QBER TU MOT MAU CONG KHAI SO SANH
# ============================================================
def calculate_qber(alice_sifted, bob_sifted, sample_ratio=0.2):
    """
    Trich ngau nhien mot ty le (mac dinh 20%) trong khoa tho da sift
    ra de "cong khai" so sanh giua Alice va Bob, tinh ty le loi bit
    luong tu (QBER) tu mau do. Phan con lai (KHONG nam trong mau) tro
    thanh khoa bi mat cuoi cung - vi bat ky bit nao da duoc cong khai
    so sanh deu khong con an toan de dung lam khoa nua, du no dung
    hay sai, nen BAT BUOC phai loai bo khoi khoa cuoi cung.

    Args:
        alice_sifted: khoa tho cua Alice (sau sift_keys()).
        bob_sifted: khoa tho cua Bob, cung do dai voi alice_sifted.
        sample_ratio: ty le (0.0 - 1.0) so bit duoc trich mau de cong
            khai so sanh. Mac dinh 0.2 (20%).

    Returns:
        tuple (qber_percent, final_secret_key):
            qber_percent: ty le loi (%) tren mau da so sanh, kieu float.
                Tra ve 0.0 neu khoa tho rong hoac mau rong (khong du
                du lieu de uoc luong).
            final_secret_key: list bit con lai SAU KHI da bo di cac
                bit thuoc mau cong khai - day la khoa thuc su dung
                duoc, lay tu phia Alice (quy uoc Alice la ben giu ban
                "chinh thuc" cua khoa trong mo phong nay).

    Raises:
        ValueError: neu 2 mang khoa tho khong cung do dai, hoac
            sample_ratio khong nam trong khoang (0, 1].
    """
    if len(alice_sifted) != len(bob_sifted):
        raise ValueError(
            f"alice_sifted va bob_sifted phai cung do dai, hien tai: "
            f"{len(alice_sifted)} va {len(bob_sifted)}"
        )
    if not (0 < sample_ratio <= 1):
        raise ValueError(f"sample_ratio phai trong khoang (0, 1], hien tai: {sample_ratio}")

    n = len(alice_sifted)
    if n == 0:
        return 0.0, []

    sample_size = max(1, round(n * sample_ratio))
    sample_size = min(sample_size, n)  # phong truong hop lam tron vuot qua do dai thuc te

    sample_indices = set(random.sample(range(n), sample_size))

    error_count = sum(
        1 for i in sample_indices if alice_sifted[i] != bob_sifted[i]
    )
    qber_percent = (error_count / sample_size) * 100

    final_secret_key = [
        bit for i, bit in enumerate(alice_sifted) if i not in sample_indices
    ]

    return qber_percent, final_secret_key


# ============================================================
# KHOI KIEM THU DOC LAP - chi chay khi goi truc tiep file nay,
# khong chay khi module duoc import tu noi khac.
# ============================================================
if __name__ == "__main__":
    random.seed(42)  # co dinh seed de ket qua demo nay lap lai giong nhau moi lan chay

    NUM_RAW_BITS = 512  # khop dung QKD_PARAMS["KEY_LENGTH_RAW"] trong config.py cua du an -
                         # quy mo thuc te nay cho QBER uoc luong on dinh hon nhieu so voi
                         # bo du lieu qua nho (vd 20-200 bit), it bi anh huong boi may rui khi lay mau

    print("=" * 60)
    print(f"KICH BAN 1: Kenh sach (khong nghe len), {NUM_RAW_BITS} bit tho - ky vong QBER ~ 0%")
    print("=" * 60)

    alice_bases_1 = [random.choice(['+', 'x']) for _ in range(NUM_RAW_BITS)]
    bob_bases_1 = [random.choice(['+', 'x']) for _ in range(NUM_RAW_BITS)]
    alice_bits_1 = [random.randint(0, 1) for _ in range(NUM_RAW_BITS)]

    # Kenh sach: bob doc DUNG bit da gui moi khi trung basis; lech
    # basis thi ket qua ngau nhien (se bi sift_keys() loai bo, khong
    # anh huong QBER nen gia tri cu the khong quan trong).
    bob_bits_1 = [
        alice_bits_1[i] if alice_bases_1[i] == bob_bases_1[i] else random.randint(0, 1)
        for i in range(NUM_RAW_BITS)
    ]

    a_sifted_1, b_sifted_1, matched_1 = sift_keys(alice_bases_1, bob_bases_1, alice_bits_1, bob_bits_1)
    print(f"So bit ban dau         : {NUM_RAW_BITS}")
    print(f"So bit sau sifting     : {len(a_sifted_1)}  (~50% ly thuyet, vi 2 basis ngau nhien doc lap)")

    qber_1, final_key_1 = calculate_qber(a_sifted_1, b_sifted_1, sample_ratio=0.2)
    print(f"QBER uoc luong         : {qber_1:.2f}%")
    print(f"Khoa bi mat cuoi cung  : dai {len(final_key_1)} bit")
    print(f"  10 bit dau cua khoa  : {final_key_1[:10]}")

    print()
    print("=" * 60)
    print(f"KICH BAN 2: Co nghe len (Eve chen giua), {NUM_RAW_BITS} bit tho - ky vong QBER cao")
    print("=" * 60)

    # Mo phong tan cong intercept-resend: tai moi vi tri basis trung,
    # Eve co 25% kha nang lam sai lech bit doc duoc cua Bob - dung
    # dung ty le loi ly thuyet cua kieu tan cong nay tren BB84.
    alice_bases_2 = list(alice_bases_1)
    bob_bases_2 = list(bob_bases_1)
    alice_bits_2 = list(alice_bits_1)
    bob_bits_2 = list(bob_bits_1)

    matched_positions_2 = [i for i in range(NUM_RAW_BITS) if alice_bases_2[i] == bob_bases_2[i]]
    flip_positions = [i for i in matched_positions_2 if random.random() < 0.25]
    for i in flip_positions:
        bob_bits_2[i] = 1 - bob_bits_2[i]  # dao nguoc bit, mo phong nhieu do Eve gay ra

    a_sifted_2, b_sifted_2, matched_2 = sift_keys(alice_bases_2, bob_bases_2, alice_bits_2, bob_bits_2)
    print(f"So bit sau sifting     : {len(a_sifted_2)}")
    print(f"So bit bi Eve lam sai  : {len(flip_positions)} / {len(matched_positions_2)} vi tri basis trung"
          f" (~{100*len(flip_positions)/len(matched_positions_2):.1f}%)")

    qber_2, final_key_2 = calculate_qber(a_sifted_2, b_sifted_2, sample_ratio=0.2)
    print(f"QBER uoc luong         : {qber_2:.2f}%")
    print(f"Khoa bi mat cuoi cung  : dai {len(final_key_2)} bit")

    QBER_THRESHOLD = 11.0
    if qber_2 > QBER_THRESHOLD:
        print(f"=> QBER vuot nguong an toan {QBER_THRESHOLD}% - nghi ngo co nghe len, nen HUY khoa nay.")
    else:
        print(f"=> QBER duoi nguong an toan {QBER_THRESHOLD}% - kenh duoc xem la an toan.")
