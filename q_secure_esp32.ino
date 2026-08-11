/*
  q_secure_esp32.ino
  ===================
  Sketch nap cho ESP32 trong du an Q-SECURE.

  Chuc nang:
    - Nhan lenh goc quay Servo tu may tinh qua Serial, dinh dang:
          "SERVO:<goc>\n"      vd: "SERVO:90\n"
      Chi chap nhan 4 gia tri goc: 0, 45, 90, 135 (khop voi
      VALID_SERVO_ANGLES ben phia Python trong hardware_serial.py).
    - Lien tuc doc gia tri cam bien LDR va gui ve may tinh, dinh dang:
          "LDR:<gia_tri>\n"    vd: "LDR:512\n"
      Gui theo chu ky co dinh, KHONG dung delay() de khong lam "dung"
      viec doc lenh Servo den tu may tinh cung luc.

  Ket noi phan cung (chinh lai theo mach thuc te cua ban):
    - Servo -> chan SERVO_PIN (bat ky chan ho tro PWM)
    - LDR   -> chan LDR_PIN (chan ADC, vd GPIO34 - chi doc, khong ho
               tro output - phu hop lam chan cam bien analog)

  Thu vien can cai (qua Arduino IDE > Tools > Manage Libraries):
    - "ESP32Servo" (KHONG dung thu vien Servo.h mac dinh cua Arduino -
      thu vien do khong tuong thich tot voi ESP32; ESP32Servo la ban
      thay the chuan cho board ESP32).
*/

#include <ESP32Servo.h>

// ============================================================
// 1. CAU HINH CHAN & THONG SO
// ============================================================
const int SERVO_PIN = 18;   // chan dieu khien Servo (PWM)
const int LDR_PIN = 34;      // chan doc cam bien LDR (ADC, input-only)

// Chu ky gui gia tri LDR ve may tinh (mili-giay). Dung millis() thay vi
// delay() de vong lap loop() khong bi "dung hinh", van kip thoi doc
// lenh Servo moi den tu Serial trong luc cho.
const unsigned long LDR_SEND_INTERVAL_MS = 200;

// Danh sach goc Servo hop le - PHAI khop voi VALID_SERVO_ANGLES trong
// hardware_serial.py ben phia Python.
const int VALID_ANGLES[] = {0, 45, 90, 135};
const int VALID_ANGLES_COUNT = 4;

Servo myServo;
String inputBuffer = "";          // tich luy ky tu Serial cho den khi gap '\n'
unsigned long lastLdrSendTime = 0;

// ============================================================
// 2. KIEM TRA GOC CO NAM TRONG DANH SACH HOP LE KHONG
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
// 3. XU LY 1 DONG LENH DA NHAN TRON VEN (dinh dang "SERVO:<goc>")
// ============================================================
void handleCommand(String line) {
  line.trim();  // bo ky tu xuong dong / khoang trang du thua

  if (line.startsWith("SERVO:")) {
    String valuePart = line.substring(6);  // bo tien to "SERVO:"
    int angle = valuePart.toInt();

    // Luu y: String::toInt() tra ve 0 ca khi chuoi khong phai so hop
    // le (vd chuoi rong hoac ky tu la) - vi "SERVO:0" van la lenh hop
    // le, khong the dung "angle != 0" de kiem tra loi ma phai doi
    // chieu qua isValidAngle().
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
// 4. DOC SERIAL KHONG CHAN (non-blocking): gom ky tu vao buffer,
//    chi xu ly khi da nhan du 1 dong hoan chinh (gap '\n').
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

      // Chong tran buffer neu nhan phai du lieu nhieu/nhieu ma khong
      // co ky tu '\n' ket thuc (vd nhieu tin hieu tren day Serial).
      if (inputBuffer.length() > 64) {
        inputBuffer = "";
      }
    }
  }
}

// ============================================================
// 5. GUI GIA TRI LDR DINH KY - dung millis(), KHONG dung delay()
// ============================================================
void sendLdrReadingIfDue() {
  unsigned long now = millis();
  if (now - lastLdrSendTime >= LDR_SEND_INTERVAL_MS) {
    int ldrValue = analogRead(LDR_PIN);
    Serial.print("LDR:");
    Serial.println(ldrValue);
    lastLdrSendTime = now;
  }
}

// ============================================================
// SETUP / LOOP
// ============================================================
void setup() {
  Serial.begin(115200);

  myServo.attach(SERVO_PIN);
  myServo.write(0);  // vi tri mac dinh khi vua khoi dong

  inputBuffer.reserve(64);  // cap phat truoc bo nho cho buffer, tranh cap phat lai lien tuc
}

void loop() {
  readSerialCommands();      // uu tien xu ly lenh Servo den tu may tinh truoc
  sendLdrReadingIfDue();     // sau do moi kiem tra co den luc gui LDR chua
}
