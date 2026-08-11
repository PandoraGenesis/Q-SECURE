/*
  q_secure_alice_esp32c3.ino
  ===========================
  Nap cho ESP32-C3 Super Mini gan voi MAY HA (Alice - tram gui).

  Chuc nang DUY NHAT cua board nay: nhan lenh goc quay Servo tu may
  tinh qua Serial (dinh dang "SERVO:<goc>\n", vi du "SERVO:90\n"),
  xoay Servo den dung goc do de mo phong buoc "phan cuc photon" ben
  phia Alice. Board nay KHONG doc cam bien LDR - viec do la cua
  ESP32 gan voi may Son (xem file q_secure_bob_esp32c3.ino).

  Board: ESP32-C3 Super Mini

  Ket noi phan cung:
    - Servo, day tin hieu (thuong mau vang/cam) -> GPIO4
    - Servo, day nguon (do)                      -> 5V (hoac 3V3 tuy loai servo)
    - Servo, day mass (nau/den)                  -> GND

  Cau hinh trong Arduino IDE (menu Tools) - QUAN TRONG voi board C3
  Super Mini, khac voi ESP32 DevKit thuong:
    - Board: "ESP32C3 Dev Module"
    - USB CDC On Boot: "Enabled"
      (board nay dung cong USB gan lien ngay tren chip, KHONG co IC
      chuyen doi USB-Serial rieng nhu CH340/CP2102. Neu de
      "Disabled", Serial Monitor tren may tinh se khong nhan duoc gi
      ca du code van chay dung.)

  Thu vien can cai (Arduino IDE > Tools > Manage Libraries): "ESP32Servo".
  Luu y: ESP32Servo can ban moi de tuong thich voi ESP32 Arduino core
  ban moi (core 3.x) - neu bao loi khi bien dich lien quan LEDC, cap
  nhat ca thu vien ESP32Servo lan ESP32 board package len ban moi nhat.
*/

#include <ESP32Servo.h>

// ============================================================
// 1. CAU HINH CHAN
// ============================================================
const int SERVO_PIN = 4;   // GPIO4 - chan xuat tin hieu PWM cho Servo
                            // (chan an toan tren C3 Super Mini, khong
                            // phai chan strapping GPIO2/8/9)

// ============================================================
// 2. GOC HOP LE - PHAI khop VALID_SERVO_ANGLES trong hardware_serial.py
// ============================================================
const int VALID_ANGLES[] = {0, 45, 90, 135};
const int VALID_ANGLES_COUNT = 4;

Servo myServo;
String inputBuffer = "";   // gom ky tu Serial cho den khi gap '\n'

// ============================================================
// 3. KIEM TRA GOC CO HOP LE KHONG
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
// 4. XU LY 1 DONG LENH DA NHAN TRON VEN (dinh dang "SERVO:<goc>")
// ============================================================
void handleCommand(String line) {
  line.trim();

  if (line.startsWith("SERVO:")) {
    String valuePart = line.substring(6);  // bo tien to "SERVO:"
    int angle = valuePart.toInt();

    // String::toInt() tra ve 0 ca khi chuoi khong phai so hop le -
    // vi "SERVO:0" van la lenh dung, khong the dung "angle != 0" de
    // phat hien loi, phai kiem tra qua isValidAngle().
    if (isValidAngle(angle)) {
      myServo.write(angle);
      Serial.print("ACK:SERVO:");
      Serial.println(angle);
    } else {
      Serial.print("ERR:INVALID_ANGLE:");
      Serial.println(valuePart);
    }
  } else {
    Serial.print("ERR:UNKNOWN_CMD:");
    Serial.println(line);
  }
}

// ============================================================
// 5. DOC SERIAL KHONG CHAN (non-blocking)
// ============================================================
void readSerialCommands() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      if (inputBuffer.length() > 0) {
        handleCommand(inputBuffer);
        inputBuffer = "";
      }
    } else if (c != '\r') {
      inputBuffer += c;

      // Chong tran buffer neu nhan phai du lieu nhieu/loi khong co
      // ky tu '\n' ket thuc.
      if (inputBuffer.length() > 64) {
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

  inputBuffer.reserve(64);
}

void loop() {
  readSerialCommands();
}
