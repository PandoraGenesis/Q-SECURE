/*
  q_secure_bob_esp32c3.ino
  ==========================
  Nap cho ESP32-C3 Super Mini gan voi MAY SON (Bob - tram nhan).

  Chuc nang DUY NHAT cua board nay: lien tuc doc gia tri cam bien LDR
  va gui ve may tinh qua Serial, dinh dang "LDR:<gia_tri>\n" (vi du
  "LDR:512\n"), mo phong buoc "do photon" ben phia Bob. Board nay
  KHONG dieu khien Servo - viec do la cua ESP32 gan voi may Ha (xem
  file q_secure_alice_esp32c3.ino).

  Board: ESP32-C3 Super Mini

  Ket noi phan cung (mach chia ap - voltage divider - giua LDR va 1
  dien tro co dinh, vi du 10k):
    - 3V3        -> mot dau LDR
    - Dau con lai cua LDR -> GPIO1 (diem giua) -> mot dau dien tro 10k
    - Dau con lai cua dien tro 10k -> GND

  Cau hinh trong Arduino IDE (menu Tools) - QUAN TRONG voi board C3
  Super Mini, khac voi ESP32 DevKit thuong:
    - Board: "ESP32C3 Dev Module"
    - USB CDC On Boot: "Enabled"
      (board nay dung cong USB gan lien ngay tren chip, KHONG co IC
      chuyen doi USB-Serial rieng nhu CH340/CP2102. Neu de
      "Disabled", Serial Monitor tren may tinh se khong nhan duoc gi
      ca du code van chay dung.)

  Khong can cai them thu vien ngoai - chi dung ham analogRead() co san.
*/

// ============================================================
// 1. CAU HINH CHAN
// ============================================================
const int LDR_PIN = 1;   // GPIO1 - kenh ADC1_CH1, chan an toan tren
                          // C3 Super Mini (khong phai chan strapping
                          // GPIO2/8/9, khong trung chan USB 18/19)

// ============================================================
// 2. CAU HINH THOI GIAN GUI DU LIEU
// ============================================================
// Gui gia tri LDR ve may tinh moi 200ms. Dung millis() thay vi
// delay() de vong lap loop() khong bi "dung hinh" - de sau nay neu
// them lenh nhan tu may tinh (vd lenh doi chu ky gui) van doc kip
// thoi, khong phai cho het delay() moi xu ly duoc lenh moi.
const unsigned long LDR_SEND_INTERVAL_MS = 200;

unsigned long lastLdrSendTime = 0;

// ============================================================
// 3. GUI GIA TRI LDR DINH KY
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
  analogReadResolution(12);  // ESP32-C3: ADC 12-bit -> gia tri doc duoc trong khoang 0-4095
}

void loop() {
  sendLdrReadingIfDue();
}
