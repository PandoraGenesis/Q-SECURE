<div align="center">
  <h1>Q-SECURE</h1>
  <p><b>Simulation testbed for a Quantum Key Distribution system.</b></p>
  <p><i>Sa bàn mô phỏng hệ thống Quantum Key Distribution theo giao thức BB84.</i></p>

  ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![PyQt6](https://img.shields.io/badge/PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)
  ![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
  ![ESP32](https://img.shields.io/badge/ESP32-E7352C?style=for-the-badge&logo=espressif&logoColor=white)

 [Tiếng Việt](#tiếng-việt)  •  [English](#english) 
</div>

---

<h2 id="tiếng-việt">Tiếng Việt</h2>

Q-SECURE là một sa bàn quy mô nhỏ, được chế tạo để trình diễn cách một hệ thống Quantum Key Distribution dựa trên giao thức BB84 hoạt động trong thực tế. Dự án kết hợp một đường truyền quang học được mô phỏng với một pipeline mã hóa ảnh thực sự chạy được, để ý tưởng trừu tượng về truyền thông an toàn nhờ lượng tử trở thành thứ người xem có thể quan sát diễn ra trực tiếp trên hai trạm vật lý. Đây là sản phẩm dự thi Khoa học Kỹ thuật cấp tỉnh.

Giao thức này dựa trên việc hai bên, theo quy ước gọi là Alice và Bob, cùng thống nhất một khóa bí mật chung theo cách mà bất kỳ hành vi nghe lén nào cũng sẽ để lại dấu vết. Alice sinh ra một chuỗi bit ngẫu nhiên cùng một chuỗi basis đo ngẫu nhiên, sau đó truyền từng bit dưới dạng mã hóa lên một photon mô phỏng. Trong bản dựng này, ESP32 ở trạm của Alice chuyển mỗi lựa chọn basis thành một góc quay servo, còn ESP32 ở trạm của Bob đọc lại một giá trị tương ứng từ cảm biến LDR, đóng vai trò thay cho một bộ thu photon thật. Sau khi quá trình trao đổi hoàn tất, hai trạm công khai so sánh basis đã dùng cho từng bit — chứ không so sánh giá trị bit — và chỉ giữ lại những vị trí mà cả hai bên tình cờ chọn trùng basis. Bước này gọi là sifting. Một phần nhỏ của khóa đã sift sau đó được đem ra so sánh công khai để tính QBER; nếu tỷ lệ lỗi này vượt ngưỡng an toàn, kênh truyền bị xem là đã bị xâm phạm và khóa sẽ bị hủy thay vì đem ra sử dụng. Phần khóa còn sống sót trở thành keystream cho việc mã hóa XOR đơn giản trên một tấm ảnh, đây chính là cách dự án gắn phần trình diễn vật lý với một kết quả cụ thể, nhìn thấy được.

Hệ thống chạy trên hai máy tính độc lập trong cùng một mạng LAN, mỗi máy nối với một board ESP32 riêng qua USB. Cả hai máy chạy chung một codebase; thứ duy nhất khác nhau giữa hai máy là một file cấu hình cục bộ nhỏ, cho biết máy đó đang đóng vai trò nào.

### Các trạm

| Trạm | Vai trò | Nhiệm vụ |
| :--- | :---: | :--- |
| *Máy Hà* | Alice (gửi) | Sinh chuỗi bit/basis, điều khiển servo qua ESP32, thực hiện sifting, mã hóa ảnh gốc, gửi toàn bộ qua TCP socket. |
| *Máy Sơn* | Bob (nhận) | Chấp nhận kết nối TCP, đọc cảm biến LDR qua ESP32 của mình, tính QBER, giải mã ảnh, hiển thị kết quả. |

### Tính năng chính

* Sinh chuỗi bit và basis ngẫu nhiên làm nền tảng cho quá trình trao đổi BB84.
* Chuyển mỗi lựa chọn basis thành một góc quay servo trên ESP32, mô phỏng bước phân cực của một đường truyền QKD quang học.
* Đọc cảm biến LDR trên một luồng nền để dữ liệu đến không bao giờ làm đứng hình giao diện PyQt6.
* Chạy thuật toán sifting để chỉ giữ lại các bit mà cả hai trạm tình cờ dùng chung basis.
* Tính QBER từ một mẫu của khóa đã sift và đánh dấu kênh truyền khi tỷ lệ lỗi vượt ngưỡng đã cấu hình.
* Mã hóa và giải mã ảnh được truyền đi bằng XOR, dùng phần khóa còn sống sót làm keystream.
* Di chuyển ảnh đã mã hóa cùng metadata giữa hai trạm qua TCP socket.
* Giữ phần logic mạng và Serial chạy trên QThread riêng, tách biệt khỏi luồng giao diện.

### Chi tiết kỹ thuật

* Tầng Serial mở kết nối ESP32 ở tốc độ 115200 baud và đọc dữ liệu từ một luồng nền riêng, chuyển kết quả cảm biến sang giao diện thông qua một hàng đợi an toàn giữa các luồng thay vì một biến dùng chung.
* Một tập nhỏ các exception tự định nghĩa phân biệt rõ trường hợp cổng COM không tồn tại/đang bị chiếm dụng với trường hợp kết nối đang sống bị rớt giữa chừng, nhờ vậy hai kiểu lỗi này hiện lên khác nhau trong log thay vì gộp chung thành một lỗi mơ hồ.
* Các dòng dữ liệu bị lỗi định dạng hoặc nhiễu trả về từ ESP32 được bắt và bỏ qua ngay ở bước parse, nên một dòng dữ liệu hỏng không bao giờ làm sập cả vòng lặp đọc.
* Hai trạm dùng chung một repository; file duy nhất khác nhau giữa hai máy là một file cấu hình cục bộ, không được đưa lên Git, quy định vai trò, cổng COM, và địa chỉ IP cần kết nối tới.

### Cấu trúc dự án

```
Q-SECURE/
├── .github/workflows/
│   ├── static.yml
├── ESP32/
│   ├── q_secure_alice_esp32c3.ino
│   ├── q_secure_bob_esp32c3.ino
│   ├── q_secure_esp32.ino
├── assets/
│   ├── icons/
│   |  ├── semaphore_0.png
│   |  ├── semaphore_135.png
│   |  ├── semaphore_45.png
│   |  ├── semaphore_90.png
│   ├── sample_images/
├── config/
│   ├── config.py
│   ├── config_local.example.py
├── logs/
├── src/
│   ├── main.py
│   ├── core/             # BB84, sifting, QBER, mã hóa ảnh
│   ├── network/          # TCP client/server
│   ├── hardware/         # giao tiếp Serial với ESP32
│   ├── gui/              # giao diện PyQt6 + QThread workers
│   └── utils/
├── web
│   |  ├── favicon.svg
│   |  ├── index.html
│   |  ├── script.js
│   |  ├── style.css
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── run.bat
```

### Cài đặt & chạy chương trình

1. Clone repository về cả hai máy và mở terminal tại thư mục dự án.
2. Tạo và kích hoạt môi trường ảo, sau đó cài các thư viện đã chốt phiên bản bằng pip install -r requirements.txt.
3. Copy config_local.example.py thành config_local.py trên mỗi máy, rồi đặt vai trò (ALICE hoặc BOB), cổng COM, và — riêng phía Bob — địa chỉ IP của chính máy đó.
4. Khởi động Bob trước để trạm này đã sẵn sàng lắng nghe, rồi khởi động Alice và chọn ảnh cần gửi.
5. Chạy chương trình bằng python -m src.main, hoặc double-click run.bat sau khi đã hoàn tất các bước trên.

### Nhóm thực hiện

Dự án do Bảo Châu & Anh Khoa thực hiện cho kỳ thi Khoa học Kỹ thuật:
   + Anh Khoa: phụ trách phần cơ khí và điện tử — chế tạo sa bàn vật lý, đấu nối các board ESP32, lắp servo và cảm biến LDR
   + Bảo Châu: phụ trách phần mềm và thuật toán — logic BB84, sifting, mã hóa, mạng và giao diện PyQt6.

Giáo viên hướng dẫn: _(điền tên)_

Trường: THPT Quốc Học Quy Nhơn

### Giấy phép

Dự án được thực hiện phục vụ mục đích học tập và tham dự cuộc thi Khoa học Kỹ thuật, không nhằm mục đích thương mại. Phát hành theo giấy phép MIT, tùy theo quy định riêng của cuộc thi mà có thể điều chỉnh.

---

<h2 id="english">English</h2>

Q-SECURE is a small-scale testbed built to show how a Quantum Key Distribution system based on the BB84 protocol works in practice. The project pairs a simulated optical link with a working image encryption pipeline, so the abstract idea of quantum-secure communication turns into something a viewer can actually watch happen across two physical stations. It was built as an entry for a provincial-level science and engineering fair.

The protocol relies on two parties, conventionally called Alice and Bob, agreeing on a shared secret key in a way that reveals any eavesdropping attempt. Alice generates a random sequence of bits together with a random sequence of measurement bases, then transmits each bit encoded onto a simulated photon. In this build, the ESP32 on Alice's station turns each basis choice into a servo angle, while the ESP32 on Bob's station reads back a corresponding value from an LDR sensor, standing in for a real photon detector. Once the exchange is complete, the two stations publicly compare which basis they used for each bit — never the bit values themselves — and keep only the positions where both sides happened to agree. This step is called sifting. A small portion of the sifted key is then compared openly to compute the QBER; if that error rate climbs past the safety threshold, the channel is treated as compromised and the key is discarded rather than used. Whatever survives becomes the keystream for a straightforward XOR encryption of an image, which is how the project ties the physics demonstration back to something tangible.

The system runs across two independent computers on the same local network, each wired to its own ESP32 board over USB. Both machines run the exact same codebase; a small local configuration file is the only thing that tells each one which role to play.

### Stations

| Station | Role | Responsibilities |
| :--- | :---: | :--- |
| *Máy Hà* | Alice (sender) | Generates the bit/basis sequences, drives the servo through the ESP32, performs sifting, encrypts the source image, and sends everything over TCP socket. |
| *Máy Sơn* | Bob (receiver) | Accepts the TCP connection, reads the LDR sensor through its ESP32, computes the QBER, decrypts the image, and displays the result. |

### Core Features

* Generates the random bit and basis sequences that drive the BB84 exchange.
* Turns each basis choice into a servo angle on the ESP32, simulating the polarization step of an optical QKD link.
* Reads the LDR sensor on a background thread so incoming data never freezes the PyQt6 interface.
* Runs the sifting algorithm to keep only the bits where both stations happened to use the same basis.
* Computes the QBER from a sample of the sifted key and flags the channel once the error rate crosses the configured threshold.
* Encrypts and decrypts the transmitted image with XOR, using the surviving key as the keystream.
* Moves the encrypted image and its metadata between stations over a TCP socket.
* Keeps the networking and Serial logic on their own QThread, separate from the interface thread.

### Technical Details

* The Serial layer opens the ESP32 connection at 115200 baud and reads it from a dedicated background thread, handing sensor readings to the interface through a thread-safe queue rather than a shared variable.
* A small hierarchy of custom exceptions tells a missing or busy COM port apart from a connection that drops mid-session, so the two failure modes surface differently in the log instead of collapsing into one generic error.
* Malformed or noisy lines coming back from the ESP32 are caught and discarded at the parsing step, so a single corrupted reading never brings the read loop down.
* Both stations share one repository; the only file that differs between machines is a local, git-ignored configuration file that sets the role, the COM port, and the IP address to dial.

### Project Structure

```
Q-SECURE/
├── .github/workflows/
│   ├── static.yml
├── ESP32/
│   ├── q_secure_alice_esp32c3.ino
│   ├── q_secure_bob_esp32c3.ino
│   ├── q_secure_esp32.ino
├── assets/
│   ├── icons/
│   |  ├── semaphore_0.png
│   |  ├── semaphore_135.png
│   |  ├── semaphore_45.png
│   |  ├── semaphore_90.png
│   ├── sample_images/
├── config/
│   ├── config.py
│   ├── config_local.example.py
├── logs/
├── src/
│   ├── main.py
│   ├── core/             # BB84, sifting, QBER, mã hóa ảnh
│   ├── network/          # TCP client/server
│   ├── hardware/         # giao tiếp Serial với ESP32
│   ├── gui/              # giao diện PyQt6 + QThread workers
│   └── utils/
├── web
│   |  ├── favicon.svg
│   |  ├── index.html
│   |  ├── script.js
│   |  ├── style.css
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── run.bat
```

### Setup & Execution

1. Clone the repository onto both machines and open a terminal in the project folder.
2. Create and activate a virtual environment, then install the pinned dependencies with pip install -r requirements.txt.
3. Copy config_local.example.py to config_local.py on each machine and set the role (ALICE or BOB), the COM port, and — on Bob's side — the IP address of that machine.
4. Start Bob first so the station is already listening, then start Alice and pick the image to send.
5. Run the program with python -m src.main, or double-click run.bat once the steps above are done.

### Team

The project is built by Bao Chau & Anh Khoa for a science and engineering fair: 
   + Anh Khoa: handles the mechanical and electronics side — building the physical rig, wiring the ESP32 boards, and mounting the servo and LDR sensor
   + Bao Chau: handles the software and algorithms — the BB84 logic, sifting, encryption, networking, and the PyQt6 interface.

Supervising teacher: _(fill in)_

School: Quoc Hoc Quy Nhon High School

### License

The project was built for educational purposes and for entry into a science and engineering fair, not for commercial use. It's released under the MIT License, subject to whatever the competition's own rules require.
