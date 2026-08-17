"""
tcp_server.py
=============
Kich ban DOC LAP de kiem tra hai laptop co ket noi mang duoc voi nhau
qua TCP Socket hay khong, khi cung bat chung mot mang Wi-Fi Hotspot
di dong - chay tren MAY HA.

Day CHI la cong cu kiem thu/chan doan truoc khi chay ung dung Q-SECURE
that, KHONG lien quan va KHONG thay the cho src/network/tcp_server.py
trong du an chinh.

Cach dung:
    python tcp_server.py

Chuong trinh se hoi dia chi IP muon lang nghe (thuong de trong, dung
mac dinh 0.0.0.0 - nghia la lang nghe tren TAT CA card mang cua may
nay) va cong TCP (mac dinh 5000). Sau khi May Son ket noi vao, go tin
nhan roi Enter de gui - tin nhan hai chieu hien ra ngay lap tuc, khong
ben nao phai cho ben kia go xong moi thay duoc.
"""
import socket
import sys
import threading

DEFAULT_PORT = 5000


# ============================================================
# 1. NHAP THONG TIN TU NGUOI DUNG
# ============================================================
def prompt_bind_address():
    """Hoi dia chi IP de lang nghe va cong TCP, cho phep bo trong de dung gia tri mac dinh."""
    ip = input("Nhap dia chi IP de lang nghe (Enter de dung 0.0.0.0 - moi card mang): ").strip()
    if not ip:
        ip = "0.0.0.0"

    port_raw = input(f"Nhap cong TCP (Enter de dung mac dinh {DEFAULT_PORT}): ").strip()
    if not port_raw:
        port = DEFAULT_PORT
    else:
        try:
            port = int(port_raw)
            if not (0 < port < 65536):
                raise ValueError
        except ValueError:
            print(f"Cong '{port_raw}' khong hop le (phai la so nguyen 1-65535), dung mac dinh {DEFAULT_PORT}.")
            port = DEFAULT_PORT

    return ip, port


# ============================================================
# 2. LUONG NHAN TIN NHAN (chay song song, KHONG chan luong go ban phim)
# ============================================================
def receive_loop(conn: socket.socket, stop_event: threading.Event):
    """
    Chay tren mot luong (thread) rieng: lien tuc cho va in tin nhan tu
    phia ben kia. Tach rieng khoi luong chinh (dang doc ban phim) chinh
    la ly do bat buoc phai dung threading - neu khong, chuong trinh se
    bi "ket" o input() va khong the nhan tin nhan den cung luc.
    """
    while not stop_event.is_set():
        try:
            data = conn.recv(4096)
        except OSError:
            if not stop_event.is_set():
                print("\n[Mất kết nối] Đối phương đã ngắt hoặc cáp mạng/Wi-Fi bị gián đoạn đột ngột.")
            stop_event.set()
            break

        if not data:
            # recv() tra ve b"" nghia la doi phuong da chu dong dong ket noi (goi close()).
            print("\n[Đã ngắt kết nối] Đối phương đã chủ động đóng kết nối.")
            stop_event.set()
            break

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = repr(data)  # du lieu nhieu/khong phai text hop le - in dang raw de biet co gi den

        print(f"\n[Máy Sơn]: {text}")
        print("Bạn: ", end="", flush=True)


# ============================================================
# 3. LUONG GUI TIN NHAN (doc ban phim tren luong chinh)
# ============================================================
def send_loop(conn: socket.socket, stop_event: threading.Event):
    """Doc tu ban phim va gui di lien tuc, cho toi khi go 'exit' hoac mat ket noi."""
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
    bind_ip, port = prompt_bind_address()

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_sock.bind((bind_ip, port))
    except OSError as e:
        print(f"Không thể mở cổng {port} trên {bind_ip}: {e}")
        print("Kiểm tra: địa chỉ IP có đúng của máy này không, cổng có đang bị chương trình khác chiếm không.")
        sys.exit(1)

    server_sock.listen(1)
    print(f"Đang chờ kết nối trên {bind_ip}:{port} ...")
    print("(Máy Sơn cần chạy tcp_client.py và nhập đúng địa chỉ IP của Máy Hà trong cùng mạng Hotspot)")

    try:
        conn, addr = server_sock.accept()
    except KeyboardInterrupt:
        print("\nĐã huỷ chờ kết nối.")
        server_sock.close()
        sys.exit(0)

    print(f"Đã kết nối với Máy Sơn tại {addr[0]}:{addr[1]}")
    print("Gõ tin nhắn rồi Enter để gửi. Gõ 'exit' để thoát.\n")

    stop_event = threading.Event()

    receiver = threading.Thread(target=receive_loop, args=(conn, stop_event), daemon=True)
    receiver.start()

    send_loop(conn, stop_event)

    conn.close()
    server_sock.close()
    print("Đã đóng kết nối.")


if __name__ == "__main__":
    main()
