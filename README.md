<div align="center">

# Q-SECURE

**Simulation testbed for a Quantum Key Distribution system.**  
*Sa bàn mô phỏng hệ thống Quantum Key Distribution theo giao thức BB84.*

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![ESP32](https://img.shields.io/badge/ESP32-E7352C?style=for-the-badge&logo=espressif&logoColor=white)

[🇻🇳 Tiếng Việt](#-tiếng-việt) • [🇬🇧 English](#-english)

</div>

---

<h2 id="tiếng-việt">🇻🇳 Tiếng Việt</h2>

## 📌 Giới Thiệu Dự Án

**Q-SECURE** là một sa bàn quy mô nhỏ, được chế tạo để trình diễn cách một hệ thống **Quantum Key Distribution (QKD)** dựa trên giao thức **BB84** hoạt động trong thực tế. Dự án kết hợp đường truyền quang học mô phỏng với pipeline mã hóa ảnh thực tế, giúp ý tưởng truyền thông lượng tử trở nên trực quan và quan sát được trực tiếp trên hai trạm vật lý.

> 🏆 Dự án này tham dự cuộc thi **Khoa học Kỹ thuật**.

---

### 🔬 Nguyên Lý Hoạt Động (Giao Thức BB84)

Giao thức dựa trên việc hai bên (**Alice** và **Bob**) cùng thống nhất một khóa bí mật chung theo cách mà bất kỳ hành vi nghe lén nào cũng để lại dấu vết:

1. **Truyền tín hiệu:** Alice sinh ngẫu nhiên chuỗi bit và chuỗi cơ sở (basis), truyền từng bit dưới dạng mã hóa lên photon mô phỏng. Board ESP32 tại trạm Alice chuyển lựa chọn basis thành góc quay động cơ servo.
2. **Thu nhận tín hiệu:** ESP32 tại trạm Bob đọc giá trị từ cảm biến LDR (đóng vai trò bộ thu photon).
3. **Thương lượng cơ sở (Sifting):** Hai trạm công khai so sánh basis đã dùng (không so sánh giá trị bit) và chỉ giữ lại các bit có cùng basis.
4. **Kiểm tra an toàn (QBER):** So sánh công khai một phần nhỏ khóa đã sift để tính tỷ lệ lỗi $QBER$. Nếu $QBER > 11\%$, kênh truyền bị coi là bị xâm phạm và khóa sẽ bị hủy.
5. **Mã hóa dữ liệu:** Phần khóa an toàn còn lại làm keystream để mã hóa XOR một tấm ảnh thực tế.

---

### 🖥️ Các Trạm Trong Hệ Thống

Hệ thống vận hành trên 2 máy tính độc lập trong cùng mạng LAN, nối với board ESP32 qua cổng USB:

| Trạm | Vai Trò | Nhiệm Vụ |
| :--- | :---: | :--- |
| **Máy Hà** | **Alice** (gửi) | Sinh chuỗi bit/basis, điều khiển servo qua ESP32, thực hiện sifting, mã hóa ảnh gốc và gửi qua TCP socket. |
| **Máy Sơn** | **Bob** (nhận) | Lắng nghe TCP connection, đọc cảm biến LDR qua ESP32, tính $QBER$, giải mã ảnh và hiển thị kết quả. |

---

### ✨ Tính Năng Chính

* **Sinh khóa ngẫu nhiên:** Khởi tạo chuỗi bit và basis ngẫu nhiên chuẩn bị cho quá trình trao đổi BB84.
* **Điều khiển phần cứng:** Chuyển đổi basis thành góc quay servo trên ESP32 mô phỏng bước phân cực quang học.
* **Xử lý đa luồng (Multi-threading):** Đọc cảm biến LDR trên luồng nền (`QThread`), giữ giao diện PyQt6 mượt mà.
* **Sifting & QBER:** Tự động lọc khóa và đánh giá ngưỡng an toàn $QBER \le 11\%$.
* **Mã hóa ảnh XOR:** Mã hóa/giải mã ảnh thời gian thực bằng khóa lượng tử thu được.
* **Truyền dữ liệu mạng:** Di chuyển ảnh đã mã hóa cùng metadata giữa hai trạm qua TCP Socket.

---

### 🛠️ Chi Tiết Kỹ Thuật

* **Serial Communication:** Tần số 115200 baud, truyền nhận dữ liệu qua hàng đợi an toàn thread-safe.
* **Xử lý ngoại lệ:** Phân biệt rõ ràng lỗi mất kết nối cổng COM cứng với lỗi rớt mạng giữa chừng thông qua Custom Exception Hierarchy.
* **Lọc nhiễu dữ liệu:** Tự động bắt và loại bỏ các dòng dữ liệu nhiễu/lỗi định dạng từ ESP32 mà không làm dừng chương trình.
* **Kiến trúc đồng nhất:** Hai trạm dùng chung codebase, cấu hình linh hoạt qua file `config_local.py`.

---

### 📁 Cấu Trúc Thư Mục

```text
Q-SECURE/
├── .github/workflows/      # GitHub Actions / Static workflows
├── ESP32/                  # Mã nguồn C/C++ cho board ESP32
│   ├── q_secure_alice_esp32c3.ino
│   ├── q_secure_bob_esp32c3.ino
│   └── q_secure_esp32.ino
├── PyQt6/                  # Giao diện đồ họa PyQt6 & Logic ứng dụng
│   ├── src/
│   │   ├── core/           # Thuật toán BB84, Sifting, QBER, Mã hóa XOR
│   │   ├── gui/            # Giao diện chính, Widgets, QThread Workers
│   │   ├── hardware/       # Quản lý kết nối Serial ESP32
│   │   └── network/        # Quản lý kết nối TCP Client/Server
│   ├── esp32_serial.py     # Module quản lý giao tiếp Serial giữa ứng dụng PyQt6 và vi điều khiển ESP32
│   ├── image_crypto.py     # Module xử lý mã hóa và giải mã dữ liệu hình ảnh bằng thuật toán XOR
│   ├── qkd_logic.py        # Module thực thi thuật toán và logic lõi của giao thức BB84 (QKD)
│   └── qsecure_app.py      # Entry point khởi chạy GUI
├── src/
│   ├── main.py
│   ├── core/               # BB84, sifting, QBER, mã hóa ảnh
│   ├── network/            # TCP client/server
│   ├── hardware/           # Giao tiếp Serial với ESP32
│   ├── gui/                # Giao diện PyQt6 + QThread workers
│   └── utils/
├── web/                    # Giao diện web mô phỏng / báo cáo trực tuyến (GitHub Pages)
│   ├── favicon.svg         # Biểu tượng biểu trưng (Icon) hiển thị trên thẻ trình duyệt
│   ├── index.html          # Cấu trúc khung nội dung HTML chính của trang web
│   ├── script.js           # Logic xử lý tương tác, dữ liệu và hiệu ứng giao diện (JavaScript)
│   └── style.css           # Định dạng kiểu dáng, màu sắc và bố cục giao diện (CSS)
├── assets/                 # Biểu tượng semaphore & ảnh mẫu
├── logs/                   # Nhật ký hoạt động hệ thống
├── config.py
├── config_local.example.py
├── src/
├── requirements.txt        # Danh sách thư viện phụ thuộc
└── run.bat                 # Script khởi chạy nhanh trên Windows
```

---

### 🚀 Hướng Dẫn Cài Đặt & Vận Hành

#### 1. Cài Đặt Môi Trường

- Clone repository về máy:
```bash
    git clone https://github.com/username/Q-SECURE.git
    cd Q-SECURE
```

- Tạo và kích hoạt môi trường ảo:
```bash
    python -m venv venv
    venv\Scripts\activate
```

- Cài đặt thư viện phụ thuộc:
```bash
    pip install -r requirements.txt
```

---

#### 2. Khởi Chạy Giao Diện Đồ Họa (PyQt6 GUI — Khuyên Dùng)

```bash
    cd PyQt6
    python qsecure_app.py
```

- **Trạm Alice (Gửi):** Chọn vai trò `Alice (Máy Hà — gửi)`, chọn cổng COM kết nối ESP32 (hoặc `Không dùng phần cứng`), chọn ảnh gốc và nhấn **Bắt đầu truyền tin**.
- **Trạm Bob (Nhận):** Chọn vai trò `Bob (Máy Sơn — nhận)`, nhập IP/Port của trạm Alice và nhấn **Bắt đầu truyền tin**.

---

#### 3. Khởi Chạy Giao Diện Dòng Lệnh (CLI Mode)

- Sao chép cấu hình:
```bash
    cp config_local.example.py config_local.py
```


- Chỉnh sửa vai trò (`ALICE`/`BOB`) và IP trong `config_local.py`.

- Khởi động trạm Bob trước, sau đó khởi động Alice:
```bash
    python -m src.main
```

### 👥 Nhóm Thực Hiện
- Dự án do Bảo Châu & Anh Khoa thực hiện cho kỳ thi Khoa học Kỹ thuật:
   + Anh Khoa: phụ trách phần cơ khí và điện tử — chế tạo sa bàn vật lý, đấu nối các board ESP32, lắp servo và cảm biến LDR
   + Bảo Châu: phụ trách phần mềm và thuật toán — logic BB84, sifting, mã hóa, mạng và giao diện PyQt6.

- Giáo viên hướng dẫn: _(điền tên)_

- Trường: THPT Quốc Học Quy Nhơn

### 📜 Giấy Phép
Dự án được thực hiện phục vụ mục đích học tập và tham dự cuộc thi Khoa học Kỹ thuật, không nhằm mục đích thương mại. Phát hành theo giấy phép MIT, tùy theo quy định riêng của cuộc thi mà có thể điều chỉnh.

---

<h2 id="english">🇬🇧 English</h2>

## 📌 Project Introduction

**Q-SECURE** is a small-scale demo model built to demonstrate how a **Quantum Key Distribution (QKD)** system based on the **BB84** protocol works in practice. The project combines a simulated optical link with a real image-encryption pipeline, making the idea of quantum communication intuitive and directly observable across two physical stations.

> 🏆 This project submitted for the **Science and Engineering Fair** competition.

---

### 🔬 Operating Principle (BB84 Protocol)

The protocol relies on two parties (**Alice** and **Bob**) agreeing on a shared secret key in a way that any eavesdropping leaves a detectable trace:

1. **Signal transmission:** Alice randomly generates a bit string and a basis string, sending each bit encoded onto a simulated photon. The ESP32 board at Alice's station converts the basis choice into a servo motor rotation angle.
2. **Signal reception:** The ESP32 at Bob's station reads the value from an LDR sensor (acting as the photon receiver).
3. **Basis reconciliation (Sifting):** The two stations publicly compare the bases used (not the bit values themselves) and keep only the bits where the bases matched.
4. **Security check (QBER):** A small portion of the sifted key is publicly compared to calculate the error rate $QBER$. If $QBER > 11\%$, the channel is considered compromised and the key is discarded.
5. **Data encryption:** The remaining secure portion of the key is used as a keystream to XOR-encrypt a real image.

---

### 🖥️ Stations in the System

The system runs on two independent computers on the same LAN, each connected to an ESP32 board via USB:

| Station | Role | Task |
| :--- | :---: | :--- |
| **Hà's Machine** | **Alice** (sender) | Generates the bit/basis strings, controls the servo via ESP32, performs sifting, encrypts the original image, and sends it over a TCP socket. |
| **Sơn's Machine** | **Bob** (receiver) | Listens for the TCP connection, reads the LDR sensor via ESP32, computes $QBER$, decrypts the image, and displays the result. |

---

### ✨ Key Features

* **Random key generation:** Initializes random bit and basis strings in preparation for the BB84 exchange.
* **Hardware control:** Converts basis choices into servo rotation angles on the ESP32, simulating an optical polarization step.
* **Multi-threading:** Reads the LDR sensor on a background thread (`QThread`), keeping the PyQt6 UI smooth and responsive.
* **Sifting & QBER:** Automatically filters the key and evaluates it against the $QBER \le 11\%$ safety threshold.
* **XOR image encryption:** Encrypts/decrypts images in real time using the derived quantum key.
* **Network data transfer:** Moves the encrypted image and its metadata between the two stations over a TCP socket.

---

### 🛠️ Technical Details

* **Serial Communication:** Baud rate 115200, with data sent/received through a thread-safe queue.
* **Exception handling:** Clearly distinguishes hard COM-port disconnection errors from mid-session network drops using a custom exception hierarchy.
* **Data noise filtering:** Automatically catches and discards noisy or malformed data lines from the ESP32 without stopping the program.
* **Unified architecture:** Both stations share the same codebase, configured flexibly via the `config_local.py` file.

---

### 📁 Directory Structure

```text
Q-SECURE/
├── .github/workflows/      # GitHub Actions / Static workflows
├── ESP32/                  # C/C++ source code for the ESP32 board
│   ├── q_secure_alice_esp32c3.ino
│   ├── q_secure_bob_esp32c3.ino
│   └── q_secure_esp32.ino
├── PyQt6/                  # PyQt6 GUI & application logic
│   ├── src/
│   │   ├── core/           # BB84 algorithm, Sifting, QBER, XOR encryption
│   │   ├── gui/            # Main interface, widgets, QThread workers
│   │   ├── hardware/       # ESP32 serial connection management
│   │   └── network/        # TCP client/server connection management
│   ├── esp32_serial.py     # Module managing serial communication between the PyQt6 app and the ESP32 microcontroller
│   ├── image_crypto.py     # Module handling image encryption/decryption via the XOR algorithm
│   ├── qkd_logic.py        # Module implementing the core BB84 (QKD) protocol algorithm and logic
│   └── qsecure_app.py      # GUI entry point
├── src/
│   ├── main.py
│   ├── core/               # BB84, sifting, QBER, image encryption
│   ├── network/            # TCP client/server
│   ├── hardware/           # Serial communication with ESP32
│   ├── gui/                # PyQt6 interface + QThread workers
│   └── utils/
├── web/                    # Simulation / online report web interface (GitHub Pages)
│   ├── favicon.svg         # Site icon shown in the browser tab
│   ├── index.html          # Main HTML content structure of the site
│   ├── script.js           # Interaction, data, and UI-effect logic (JavaScript)
│   └── style.css           # Styling, colors, and layout (CSS)
├── assets/                 # Semaphore icons & sample images
├── logs/                   # System activity logs
├── config.py
├── config_local.example.py
├── src/
├── requirements.txt        # List of dependencies
└── run.bat                 # Quick-start script for Windows
```

---

### 🚀 Installation & Operation Guide

#### 1. Environment Setup

- Clone the repository:
```bash
    git clone https://github.com/username/Q-SECURE.git
    cd Q-SECURE
```

- Create and activate a virtual environment:
```bash
    python -m venv venv
    venv\Scripts\activate
```

- Install dependencies:
```bash
    pip install -r requirements.txt
```

---

#### 2. Launching the Graphical Interface (PyQt6 GUI — Recommended)

```bash
    cd PyQt6
    python qsecure_app.py
```

- **Alice Station (Sender):** Select the role `Alice (Hà's Machine — sender)`, choose the COM port connected to the ESP32 (or `No hardware`), select the original image, and click **Start Transmission**.
- **Bob Station (Receiver):** Select the role `Bob (Sơn's Machine — receiver)`, enter Alice station's IP/Port, and click **Start Transmission**.

---

#### 3. Launching the Command-Line Interface (CLI Mode)

- Copy the configuration file:
```bash
    cp config_local.example.py config_local.py
```

- Edit the role (`ALICE`/`BOB`) and IP address in `config_local.py`.

- Start the Bob station first, then start Alice:
```bash
    python -m src.main
```

### 👥 Project Team
- Project carried out by Bảo Châu & Anh Khoa for the Science and Engineering Fair:
   + Anh Khoa: mechanical and electronics lead — built the physical demo model, wired the ESP32 boards, mounted the servos and LDR sensors
   + Bảo Châu: software and algorithms lead — BB84 logic, sifting, encryption, networking, and the PyQt6 interface.

- Supervising teacher: _(fill in name)_

- School: Quoc Hoc Quy Nhon High School

### 📜 License
This project was created for educational purposes and participation in the Science and Engineering Fair competition, not for commercial purposes. Released under the MIT license, subject to adjustment per the competition's own rules.
