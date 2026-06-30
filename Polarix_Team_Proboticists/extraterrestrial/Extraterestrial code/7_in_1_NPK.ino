#include <SoftwareSerial.h>

// RS485 Connections (UNO)
const byte ROPin = 2;   // RO -> D2  (RX)
const byte DIPin = 3;   // DI -> D3  (TX)
const byte DEPin = 6;   // DE
const byte REPin = 7;   // RE

SoftwareSerial max485Serial(ROPin, DIPin);

// Your Modbus requests (keep as-is if they work with your sensor)
const byte temp_cmd[]  = { 0x01, 0x03, 0x00, 0x13, 0x00, 0x01, 0x75, 0xCF };
const byte mois_cmd[]  = { 0x01, 0x03, 0x00, 0x12, 0x00, 0x01, 0x24, 0x0F };
const byte ec_cmd[]    = { 0x01, 0x03, 0x00, 0x15, 0x00, 0x01, 0x95, 0xCE };
const byte ph_cmd[]    = { 0x01, 0x03, 0x00, 0x06, 0x00, 0x01, 0x64, 0x0B };
const byte nitro_cmd[] = { 0x01, 0x03, 0x00, 0x1E, 0x00, 0x01, 0xE4, 0x0C };
const byte phos_cmd[]  = { 0x01, 0x03, 0x00, 0x1F, 0x00, 0x01, 0xB5, 0xCC };
const byte pota_cmd[]  = { 0x01, 0x03, 0x00, 0x20, 0x00, 0x01, 0x85, 0xC0 };

byte rxBuf[7];

// ---------- RS485 Direction ----------
void rs485Tx() {
  digitalWrite(DEPin, HIGH);
  digitalWrite(REPin, HIGH);
}
void rs485Rx() {
  digitalWrite(DEPin, LOW);
  digitalWrite(REPin, LOW);
}

// ---------- Clear serial buffer ----------
void clearReceiveBuffer() {
  while (max485Serial.available()) max485Serial.read();
}

// ---------- Read one holding register (16-bit) ----------
bool readRegister16(const byte *command, byte length, uint16_t &outVal, bool debug = false) {
  clearReceiveBuffer();

  // Send request
  rs485Tx();
  delay(2);
  for (byte i = 0; i < length; i++) max485Serial.write(command[i]);
  max485Serial.flush();

  // Switch to RX
  delay(2);
  rs485Rx();

  // Receive 7 bytes with timeout
  unsigned long t0 = millis();
  byte idx = 0;
  while ((millis() - t0) < 400 && idx < 7) {
    if (max485Serial.available()) {
      rxBuf[idx++] = max485Serial.read();
    }
  }

  if (debug) {
    Serial.print("RX: ");
    for (byte i = 0; i < idx; i++) {
      if (rxBuf[i] < 16) Serial.print("0");
      Serial.print(rxBuf[i], HEX);
      Serial.print(" ");
    }
    Serial.println();
  }

  if (idx != 7) return false;

  // Basic Modbus header check: [ID=0x01][FUNC=0x03][BYTES=0x02]
  if (rxBuf[0] != 0x01) return false;
  if (rxBuf[1] != 0x03) return false;
  if (rxBuf[2] != 0x02) return false;

  outVal = ((uint16_t)rxBuf[3] << 8) | rxBuf[4];
  return true;
}

void setup() {
  Serial.begin(9600);
  max485Serial.begin(9600);

  pinMode(REPin, OUTPUT);
  pinMode(DEPin, OUTPUT);
  rs485Rx();

  delay(1500);
  Serial.println("RS485 Soil Sensor: Moisture, Temp, EC, pH, NPK");
}

void loop() {
  uint16_t moistRaw, tempRaw, ecRaw, phRaw, nRaw, pRaw, kRaw;

  bool okMoist = readRegister16(mois_cmd, sizeof(mois_cmd), moistRaw, true);
  delay(200);
  bool okTemp  = readRegister16(temp_cmd, sizeof(temp_cmd), tempRaw, true);
  delay(200);
  bool okEC    = readRegister16(ec_cmd,   sizeof(ec_cmd),   ecRaw,   true);
  delay(200);
  bool okPH    = readRegister16(ph_cmd,   sizeof(ph_cmd),   phRaw,   true);
  delay(200);
  bool okN     = readRegister16(nitro_cmd,sizeof(nitro_cmd),nRaw,    true);
  delay(200);
  bool okP     = readRegister16(phos_cmd, sizeof(phos_cmd), pRaw,    true);
  delay(200);
  bool okK     = readRegister16(pota_cmd, sizeof(pota_cmd), kRaw,    true);

  // Typical scaling for many sensors:
  float soil_mois = okMoist ? (moistRaw / 10.0f) : -1;
  float soil_temp = okTemp  ? ((int16_t)tempRaw / 10.0f) : -1; // signed temp
  float soil_ph   = okPH    ? (phRaw / 10.0f) : -1;

  Serial.println("--------------------------------------------------");

  Serial.print("Moisture: ");
  if (!okMoist) Serial.println("NA");
  else { Serial.print(soil_mois, 1); Serial.println(" %"); }

  Serial.print("Temperature: ");
  if (!okTemp) Serial.println("NA");
  else { Serial.print(soil_temp, 1); Serial.println(" C"); }

  Serial.print("EC: ");
  if (!okEC) Serial.println("NA");
  else { Serial.print(ecRaw); Serial.println(" uS/cm"); }

  Serial.print("pH: ");
  if (!okPH) Serial.println("NA");
  else { Serial.print(soil_ph, 1); Serial.println(); }

  Serial.print("Nitrogen: ");
  if (!okN) Serial.println("NA");
  else { Serial.print(nRaw); Serial.println(" mg/kg"); }

  Serial.print("Phosphorous: ");
  if (!okP) Serial.println("NA");
  else { Serial.print(pRaw); Serial.println(" mg/kg"); }

  Serial.print("Potassium: ");
  if (!okK) Serial.println("NA");
  else { Serial.print(kRaw); Serial.println(" mg/kg"); }

  delay(2000);
}
