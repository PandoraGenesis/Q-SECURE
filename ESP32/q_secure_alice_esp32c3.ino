/*
  q_secure_alice_esp32c3.ino
  ===========================
  Nap cho ESP32-C3 Super Mini gan voi MAY HA (Alice - tram gui) trong
  du an KHKT Q-SECURE.

  Chuc nang: nhan mot con so nguyen tuong trung cho goc quay Servo tu
  may tinh qua Serial USB (dinh dang thuan tuy "<goc>\n", vi du "90\n"
  - KHONG co tien to chu nao ca), chuyen doi va xoay Servo den dung
  goc do, roi phan hoi lai chuoi "OK:<goc>" de may tinh biet da quay
  xong. Chi chap nhan dung 4 gia tri goc: 0, 45, 90, 135.

  Board: ESP32-C3 Super Mini

  Ket noi phan cung:
    - Servo, day tin hieu (thuong mau vang/cam) -> GPIO4
    - Servo, day nguon (do)                      -> 5V (hoac 3V3 tuy loai servo)
    - Servo, day mass (nau/den)                  -> GND

  Luu y ve chan GPIO4: KHONG dung GPIO2 nhu vi du tham khao, vi day la
  1 trong cac chan "strapping" cua ESP32-C3 (chan duoc doc de quyet
  dinh che do khoi dong ngay luc reset). Cam tin hieu Servo vao do co
  the gay khoi dong sai che do o mot so mach. GPIO4 khong phai chan
  strapping, an toan de dung lam tin hieu dieu khien.

  Cau hinh trong Arduino IDE (menu Tools) - BAT BUOC phai dung voi
  board C3 Super Mini, khac voi ESP32 DevKit thuong:
    - Board: "ESP32C3 Dev Module"
    - USB CDC On Boot: "Enabled"
      (board nay dung cong USB gan lien ngay tren chip, KHONG co IC
      chuyen doi USB-Serial rieng nhu CH340/CP2102. Neu de "Disabled",
      Serial Monitor tren may tinh se KHONG nhan duoc gi ca, du code
      van bien dich va chay dung.)

  Thu vien can cai (Arduino IDE > Tools > Manage Libraries): "ESP32Servo".
  Thu vien nay dung LEDC (bo bam xung PWM phan cung cua ESP32) o phia
  sau de tao tin hieu dieu khien Servo, da tuong thich voi loi ESP32-C3.
  Luu y: can ban ESP32Servo moi de tuong thich voi ESP32 Arduino core
  ban moi (core 3.x) - neu bao loi bien dich lien quan LEDC, cap nhat
  ca thu vien ESP32Servo lan ESP32 board package len ban moi nhat.
*/

#include <ESP32Servo.h>

// ============================================================
// 1. CAU HINH CHAN
// ============================================================
const int SERVO_PIN = 4;   // GPIO4 - chan xuat tin hieu PWM cho Servo (an toan, khong phai chan strapping)

// ============================================================
// 2. GOC HOP LE - PHAI khop VALID_SERVO_ANGLES ben phia Python
// ============================================================
const int VALID_ANGLES[] = {0, 45, 90, 135};
const int VALID_ANGLES_COUNT = 4;

Servo myServo;
String inputBuffer = "";   // gom ky tu Serial cho den khi gap '\n'

// ============================================================
// 3. KIEM TRA GOC CO NAM TRONG DANH SACH HOP LE KHONG
// ============================================================
bool isValidAngle(int angle) {
  for (int i = 0; i < VALID_ANGLES_COUNT; i++) {
    if (VALID_ANGLES[i] == angle) {
      return true;
    }
  }
  return false;
}

// ============================================================
// 4. KIEM TRA CHUOI CO PHAI TOAN CHU SO KHONG
//    Can ham rieng vi String::toInt() tra ve 0 CA KHI chuoi khong
//    phai so hop le (vd chuoi rong, chuoi chua chu cai) - neu chi
//    dua vao toInt() se khong phan biet duoc "0" that voi rac.
// ============================================================
bool isNumericString(const String &s) {
  if (s.length() == 0) return false;
  for (unsigned int i = 0; i < s.length(); i++) {
    if (!isDigit(s.charAt(i))) return false;
  }
  return true;
}

// ============================================================
// 5. XU LY 1 DONG LENH DA NHAN TRON VEN - dinh dang thuan tuy "<goc>"
// ============================================================
void handleCommand(String line) {
  line.trim();  // bo ky tu xuong dong / khoang trang du thua con sot

  if (!isNumericString(line)) {
    Serial.print("ERR:NOT_A_NUMBER:");
    Serial.println(line);
    return;
  }

  int angle = line.toInt();

  if (isValidAngle(angle)) {
    myServo.write(angle);
    Serial.print("OK:");
    Serial.println(angle);
  } else {
    Serial.print("ERR:INVALID_ANGLE:");
    Serial.println(angle);
  }
}

// ============================================================
// 6. DOC SERIAL KHONG CHAN (non-blocking)
// ============================================================
void readSerialCommands() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      if (inputBuffer.length() > 0) {
        handleCommand(inputBuffer);
      }
      // Xoa bo dem NGAY sau khi xu ly xong 1 lenh (du lenh hop le hay
      // loi), de san sang tiep nhan lenh ke tiep tu dau, khong de sot
      // lai ky tu cu lam hong lan doc sau.
      inputBuffer = "";
    } else if (c != '\r') {
      inputBuffer += c;

      // Chong tran buffer neu nhan phai du lieu nhieu/loi khong co
      // ky tu '\n' ket thuc.
      if (inputBuffer.length() > 32) {
        inputBuffer = "";
      }
    }
  }
}

// ============================================================
// SETUP / LOOP
// ============================================================
void setup() {
  Serial.begin(115200);

  myServo.attach(SERVO_PIN);
  myServo.write(0);  // vi tri mac dinh khi vua khoi dong

  inputBuffer.reserve(32);
}

void loop() {
  readSerialCommands();
}
