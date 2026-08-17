/*
  q_secure_bob_esp32c3.ino
  ==========================
  Nap cho ESP32-C3 Super Mini gan voi MAY SON (Bob - tram nhan) trong
  du an KHKT Q-SECURE.

  Khac voi ban truoc (chi doc LDR dinh ky, khong co Servo), board nay
  gio dam nhan CA HAI nhiem vu: xoay Servo (dai dien cho kinh phan
  tich/basis do cua Bob) VA doc cam bien LDR ngay sau khi xoay xong -
  vi ve mat vat ly, ket qua do sang chi co y nghia SAU KHI kinh phan
  tich da o dung goc.

  Luong hoat dong khi nhan 1 lenh goc tu may tinh:
    1. Nhan so nguyen goc (dinh dang thuan tuy "<goc>\n", vi du "90\n",
       giong het giao thuc ben May Ha - khong co tien to chu).
    2. Xoay Servo den dung goc do.
    3. Dung lai cho 200ms de anh sang/co hoc on dinh (servo vua quay
       xong con rung nhe, can thoi gian de LDR khong doc phai gia tri
       nhieu do dao dong co hoc).
    4. Doc gia tri LDR, gui ve may tinh dinh dang "LDR:<gia_tri>\n".

  Board nay KHONG tu dong gui LDR dinh ky nhu ban truoc - chi gui
  DUNG 1 lan sau moi lenh goc nhan duoc, dong vai tro vua la xac nhan
  da xoay xong vua la ket qua do.

  Board: ESP32-C3 Super Mini

  Ket noi phan cung:
    - Servo, day tin hieu (thuong mau vang/cam) -> GPIO4
    - Servo, day nguon (do)                      -> 5V (hoac 3V3 tuy loai servo)
    - Servo, day mass (nau/den)                  -> GND
    - LDR (mach chia ap voltage divider voi 1 dien tro co dinh, vi du 10k):
        3V3 -> mot dau LDR -> diem giua (GPIO1) -> dien tro 10k -> GND

  Luu y ve chan: GPIO4 va GPIO1 deu KHONG phai chan strapping cua
  ESP32-C3 (cac chan strapping can tranh la GPIO2/8/9), an toan de
  dung cho Servo va ADC.

  Cau hinh trong Arduino IDE (menu Tools) - BAT BUOC voi board C3
  Super Mini, khac voi ESP32 DevKit thuong:
    - Board: "ESP32C3 Dev Module"
    - USB CDC On Boot: "Enabled"
      (board nay dung cong USB gan lien ngay tren chip, KHONG co IC
      chuyen doi USB-Serial rieng nhu CH340/CP2102. Neu de "Disabled",
      Serial Monitor tren may tinh se KHONG nhan duoc gi ca, du code
      van bien dich va chay dung.)

  Thu vien can cai (Arduino IDE > Tools > Manage Libraries): "ESP32Servo".
*/

#include <ESP32Servo.h>

// ============================================================
// 1. CAU HINH CHAN
// ============================================================
const int SERVO_PIN = 4;   // GPIO4 - tin hieu PWM dieu khien Servo (kinh phan tich)
const int LDR_PIN = 1;      // GPIO1 - kenh ADC1_CH1, doc gia tri sang tu LDR

// ============================================================
// 2. THOI GIAN CHO ON DINH SAU KHI XOAY SERVO
// ============================================================
const unsigned long SETTLE_DELAY_MS = 200;

// ============================================================
// 3. GOC HOP LE - PHAI khop VALID_SERVO_ANGLES ben phia Python va ben May Ha
// ============================================================
const int VALID_ANGLES[] = {0, 45, 90, 135};
const int VALID_ANGLES_COUNT = 4;

Servo myServo;
String inputBuffer = "";   // gom ky tu Serial cho den khi gap '\n'

// ============================================================
// 4. KIEM TRA GOC CO HOP LE KHONG
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
// 5. KIEM TRA CHUOI CO PHAI TOAN CHU SO KHONG
//    (String::toInt() tra ve 0 ca khi chuoi khong phai so hop le,
//    nen can kiem tra rieng de phan biet "0" that voi du lieu rac).
// ============================================================
bool isNumericString(const String &s) {
  if (s.length() == 0) return false;
  for (unsigned int i = 0; i < s.length(); i++) {
    if (!isDigit(s.charAt(i))) return false;
  }
  return true;
}

// ============================================================
// 6. XU LY 1 LENH GOC DA NHAN TRON VEN
//    Xoay Servo -> cho on dinh -> doc LDR -> gui ket qua.
// ============================================================
void handleAngleCommand(String line) {
  line.trim();

  if (!isNumericString(line)) {
    Serial.print("ERR:NOT_A_NUMBER:");
    Serial.println(line);
    return;
  }

  int angle = line.toInt();

  if (!isValidAngle(angle)) {
    Serial.print("ERR:INVALID_ANGLE:");
    Serial.println(angle);
    return;
  }

  myServo.write(angle);

  // Dung dung 200ms truoc khi doc LDR - day la khoang cho co chu dich
  // (gan voi thoi diem do), nen dung delay() truc tiep la hop ly va
  // don gian nhat, khac voi vong lap nen can non-blocking o cho khac.
  delay(SETTLE_DELAY_MS);

  int ldrValue = analogRead(LDR_PIN);
  Serial.print("LDR:");
  Serial.println(ldrValue);
}

// ============================================================
// 7. DOC SERIAL KHONG CHAN (non-blocking) - gom ky tu cho den '\n'
// ============================================================
void readSerialCommands() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      if (inputBuffer.length() > 0) {
        handleAngleCommand(inputBuffer);
      }
      inputBuffer = "";  // xoa bo dem ngay sau khi xu ly, du lenh hop le hay loi
    } else if (c != '\r') {
      inputBuffer += c;

      if (inputBuffer.length() > 32) {
        inputBuffer = "";  // chong tran buffer neu nhan phai du lieu rac khong co '\n'
      }
    }
  }
}

// ============================================================
// SETUP / LOOP
// ============================================================
void setup() {
  Serial.begin(115200);
  analogReadResolution(12);  // ESP32-C3: ADC 12-bit -> gia tri doc duoc trong khoang 0-4095

  myServo.attach(SERVO_PIN);
  myServo.write(0);  // vi tri mac dinh khi vua khoi dong

  inputBuffer.reserve(32);
}

void loop() {
  readSerialCommands();
}
