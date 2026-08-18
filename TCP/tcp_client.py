"""
tcp_client.py
=============
Kich ban DOC LAP de kiem tra hai laptop co ket noi mang duoc voi nhau
qua TCP Socket hay khong, khi cung bat chung mot mang Wi-Fi Hotspot
di dong - chay tren MAY SON.

Day CHI la cong cu kiem thu/chan doan truoc khi chay ung dung Hermex
that, KHONG lien quan va KHONG thay the cho src/network/tcp_client.py
trong du an chinh.

Cach dung:
    python tcp_client.py

Chuong trinh se hoi dia chi IP cua May Ha (xem bang cach go "ipconfig"
tren May Ha, tim dong IPv4 cua card Wi-Fi) va cong TCP (mac dinh 5000).
"""
import socket
import sys
import threading

DEFAULT_PORT = 5000
CONNECT_TIMEOUT_SECONDS = 8


# ============================================================
# 1. NHAP VA KIEM TRA THONG TIN TU NGUOI DUNG
# ============================================================
def is_valid_ipv4(ip: str) -> bool:
    """Kiem tra chuoi co dung dinh dang dia chi IPv4 hop le khong (khong goi mang)."""
    try:
        socket.inet_aton(ip)
    except OSError:
        return False
    # inet_aton cho qua mot so dinh dang rut gon khong chuan (vd "192.168.1"),
    # nen kiem tra them phai co dung 4 nhom so cach nhau boi dau cham.
    return len(ip.split(".")) == 4


def prompt_server_address():
    """Hoi dia chi IP cua May Ha va cong TCP, bat nhap lai neu dinh dang IP sai."""
    while True:
        ip = input("Nhập địa chỉ IP của Máy Hà (ví dụ 192.168.43.1): ").strip()
        if is_valid_ipv4(ip):
            break
        print(f"'{ip}' không phải địa chỉ IPv4 hợp lệ (đúng dạng X.X.X.X, ví dụ 192.168.1.5). Nhập lại.")

    port_raw = input(f"Nhập cổng TCP (Enter để dùng mặc định {DEFAULT_PORT}): ").strip()
    if not port_raw:
        port = DEFAULT_PORT
    else:
        try:
            port = int(port_raw)
            if not (0 < port < 65536):
                raise ValueError
        except ValueError:
            print(f"Cổng '{port_raw}' không hợp lệ (phải là số nguyên 1-65535), dùng mặc định {DEFAULT_PORT}.")
            port = DEFAULT_PORT

    return ip, port


# ============================================================
# 2. LUONG NHAN TIN NHAN (chay song song, KHONG chan luong go ban phim)
# ============================================================
def receive_loop(conn: socket.socket, stop_event: threading.Event):
    while not stop_event.is_set():
        try:
            data = conn.recv(4096)
        except OSError:
            if not stop_event.is_set():
                print("\n[Mất kết nối] Đối phương đã ngắt hoặc cáp mạng/Wi-Fi bị gián đoạn đột ngột.")
            stop_event.set()
            break

        if not data:
            print("\n[Đã ngắt kết nối] Đối phương đã chủ động đóng kết nối.")
            stop_event.set()
            break

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = repr(data)

        print(f"\n[Máy Hà]: {text}")
        print("Bạn: ", end="", flush=True)


# ============================================================
# 3. LUONG GUI TIN NHAN (doc ban phim tren luong chinh)
# ============================================================
def send_loop(conn: socket.socket, stop_event: threading.Event):
    while not stop_event.is_set():
        try:
            message = input("Bạn: ")
        except (EOFError, KeyboardInterrupt):
            message = "exit"

        if stop_event.is_set():
            break

        if message.strip().lower() == "exit":
            print("Đang thoát...")
            stop_event.set()
            break

        try:
            conn.sendall(message.encode("utf-8"))
        except OSError:
            print("\n[Lỗi gửi] Mất kết nối khi đang gửi tin nhắn — đối phương có thể đã ngắt.")
            stop_event.set()
            break


# ============================================================
# MAIN
# ============================================================
def main():
    server_ip, port = prompt_server_address()

    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.settimeout(CONNECT_TIMEOUT_SECONDS)  # tranh treo vo han neu sai IP/khac mang

    print(f"Đang kết nối tới {server_ip}:{port} ...")
    try:
        client_sock.connect((server_ip, port))
    except socket.timeout:
        print(f"Hết thời gian chờ kết nối tới {server_ip}:{port}.")
        print("Kiểm tra: Máy Hà đã chạy tcp_server.py chưa, cả hai máy có đang bắt chung 1 mạng Hotspot không, địa chỉ IP có đúng không.")
        sys.exit(1)
    except ConnectionRefusedError:
        print(f"Máy tại {server_ip}:{port} từ chối kết nối.")
        print("Kiểm tra: Máy Hà đã chạy tcp_server.py và đúng cổng này chưa.")
        sys.exit(1)
    except OSError as e:
        print(f"Không thể kết nối tới {server_ip}:{port}: {e}")
        print("Kiểm tra lại địa chỉ IP đã nhập có đúng không.")
        sys.exit(1)

    client_sock.settimeout(None)  # bo timeout sau khi da ket noi, de recv() cho binh thuong khong bi ngat ngang
    print(f"Đã kết nối với Máy Hà tại {server_ip}:{port}")
    print("Gõ tin nhắn rồi Enter để gửi. Gõ 'exit' để thoát.\n")

    stop_event = threading.Event()

    receiver = threading.Thread(target=receive_loop, args=(client_sock, stop_event), daemon=True)
    receiver.start()

    send_loop(client_sock, stop_event)

    client_sock.close()
    print("Đã đóng kết nối.")


if __name__ == "__main__":
    main()
