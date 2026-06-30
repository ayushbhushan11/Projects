#include "Arduino.h"
#include "Wire.h"
#include "SPI.h"

#include "DFRobot_MICS.h"
#include "bmp3.h"

// ============================================================
//                 PIN + SENSOR CONFIG (MEGA)
// ============================================================

// ---- Gas / Soil / CO2 / pH ----
#define CO2_PWM_PIN   2      // MH-Z19C PWM output -> D2
#define SOIL_PIN      A0     // Soil moisture analog -> A0
#define MICS_ADC_PIN  A1     // MICS analog -> A1
#define PH_PIN        A2     // pH analog -> A2
#define MICS_PWR_PIN  7      // MICS power/enable -> D7

#define CALIBRATION_TIME  1  // minutes

DFRobot_MICS_ADC mics(MICS_ADC_PIN, MICS_PWR_PIN);

// ---- pH sensor variables ----
float calibration_value = 28.8;
int buffer_arr[10], temp;
unsigned long avgval;
float ph_act;

// ============================================================
//                      BMP3 CONFIG
// ============================================================
#define ITERATION   UINT8_C(100)
#define I2C_ADDRESS BMP3_ADDR_I2C_SEC   // BMP388/BMP390 I2C secondary address (commonly 0x77)
#define SPI_CS_PIN  SS                  // Mega SS = D53
#define USEIIC      1                   // 1 = I2C, 0 = SPI

uint8_t dev_addr;

int8_t rslt;
uint16_t settings_sel;
struct bmp3_dev dev;
struct bmp3_data data = { 0 };
struct bmp3_settings settings = { 0 };
struct bmp3_status status = { { 0 } };

// ============================================================
//                 BMP3 LOW-LEVEL INTERFACE
// ============================================================
void spi_bmp3_cs_high(void) { digitalWrite(SPI_CS_PIN, HIGH); }
void spi_bmp3_cs_low(void)  { digitalWrite(SPI_CS_PIN, LOW);  }

void bmp3_user_delay_us(uint32_t period, void *intf_ptr) {
  (void)intf_ptr;
  delayMicroseconds(period);
}

BMP3_INTF_RET_TYPE bmp3_user_i2c_read(uint8_t reg_addr, uint8_t *reg_data, uint32_t len, void *intf_ptr) {
  (void)intf_ptr;
  uint32_t i = 0;

  Wire.beginTransmission(I2C_ADDRESS);
  Wire.write(reg_addr);
  if (Wire.endTransmission(false) != 0) { // repeated start
    return -1;
  }

  Wire.requestFrom((uint8_t)I2C_ADDRESS, (uint8_t)len);
  while (Wire.available() && i < len) {
    reg_data[i++] = Wire.read();
  }
  return 0;
}

BMP3_INTF_RET_TYPE bmp3_user_i2c_write(uint8_t reg_addr, uint8_t *reg_data, uint32_t len, void *intf_ptr) {
  (void)intf_ptr;
  Wire.beginTransmission(I2C_ADDRESS);
  Wire.write(reg_addr);
  for (uint32_t i = 0; i < len; i++) {
    Wire.write(reg_data[i]);
  }
  Wire.endTransmission();
  return 0;
}

BMP3_INTF_RET_TYPE bmp3_user_spi_read(uint8_t reg_addr, uint8_t *reg_data, uint32_t len, void *intf_ptr) {
  (void)intf_ptr;
  int8_t rslt_local = 0;

  spi_bmp3_cs_high();
  spi_bmp3_cs_low();
  SPI.transfer(reg_addr | 0x80);

  for (uint32_t i = 0; i < len; i++) {
    reg_data[i] = SPI.transfer(0xFF);
  }

  spi_bmp3_cs_high();
  return rslt_local;
}

BMP3_INTF_RET_TYPE bmp3_user_spi_write(uint8_t reg_addr, uint8_t *reg_data, uint32_t len, void *intf_ptr) {
  (void)intf_ptr;
  int8_t rslt_local = 0;

  spi_bmp3_cs_high();
  spi_bmp3_cs_low();
  SPI.transfer(reg_addr & 0x7F);

  for (uint32_t i = 0; i < len; i++) {
    SPI.transfer(reg_data[i]);
  }

  spi_bmp3_cs_high();
  return rslt_local;
}

BMP3_INTF_RET_TYPE bmp3_interface_init(struct bmp3_dev *bmp3) {
  int8_t rslt_local = BMP3_OK;

  if (bmp3 != NULL) {
    if (USEIIC) bmp3->intf = BMP3_I2C_INTF;
    else       bmp3->intf = BMP3_SPI_INTF;

    if (bmp3->intf == BMP3_I2C_INTF) {
      Wire.begin();
      dev_addr = I2C_ADDRESS;
      bmp3->read = bmp3_user_i2c_read;
      bmp3->write = bmp3_user_i2c_write;
    } else {
      SPI.begin();
      dev_addr = 0;
      bmp3->read = bmp3_user_spi_read;
      bmp3->write = bmp3_user_spi_write;
    }

    bmp3->delay_us = bmp3_user_delay_us;
    bmp3->intf_ptr = &dev_addr;
  } else {
    rslt_local = BMP3_E_NULL_PTR;
  }

  return rslt_local;
}

void bmp3_check_rslt(const char api_name[], int8_t rslt_code) {
  switch (rslt_code) {
    case BMP3_OK: break;
    case BMP3_E_NULL_PTR:
      Serial.print("API:"); Serial.print(api_name); Serial.print(" Error: Null pointer; "); Serial.println(rslt_code);
      break;
    case BMP3_E_COMM_FAIL:
      Serial.print("API:"); Serial.print(api_name); Serial.print(" Error: Communication failure; "); Serial.println(rslt_code);
      break;
    case BMP3_E_INVALID_LEN:
      Serial.print("API:"); Serial.print(api_name); Serial.print(" Error: Incorrect length parameter; "); Serial.println(rslt_code);
      break;
    case BMP3_E_DEV_NOT_FOUND:
      Serial.print("API:"); Serial.print(api_name); Serial.print(" Error: Device not found; "); Serial.println(rslt_code);
      break;
    case BMP3_E_CONFIGURATION_ERR:
      Serial.print("API:"); Serial.print(api_name); Serial.print(" Error: Configuration error; "); Serial.println(rslt_code);
      break;
    case BMP3_W_SENSOR_NOT_ENABLED:
      Serial.print("API:"); Serial.print(api_name); Serial.print(" Warning: Sensor not enabled; "); Serial.println(rslt_code);
      break;
    case BMP3_W_INVALID_FIFO_REQ_FRAME_CNT:
      Serial.print("API:"); Serial.print(api_name); Serial.print(" Warning: Invalid FIFO request frame count; "); Serial.println(rslt_code);
      break;
    default:
      Serial.print("API:"); Serial.print(api_name); Serial.print(" Error: Unknown error code; "); Serial.println(rslt_code);
      break;
  }
}

// ============================================================
//                 OTHER SENSOR HELPERS
// ============================================================
int readSoilMoisturePercent(int pin) {
  int raw = analogRead(pin);               // 0..1023 on Mega
  int percent = map(raw, 1023, 0, 0, 100); // placeholder mapping
  return constrain(percent, 0, 100);
}

float readCO2_PWM(int pin) {
  unsigned long th = pulseIn(pin, HIGH, 2000000UL);
  unsigned long tl = pulseIn(pin, LOW, 2000000UL);
  if (th == 0 || tl == 0) return -1.0;

  float Th_ms = th / 1000.0;
  float T_ms  = (th + tl) / 1000.0;
  if (T_ms < 5.0) return -1.0;

  // Common MH-Z19 PWM formula
  float ppm = 5000.0 * (Th_ms - 2.0) / (T_ms - 4.0);
  if (ppm < 0) ppm = 0;
  if (ppm > 10000) ppm = 10000;
  return ppm;
}

float readPH() {
  for (int i = 0; i < 10; i++) {
    buffer_arr[i] = analogRead(PH_PIN);
    delay(30);
  }

  for (int i = 0; i < 9; i++) {
    for (int j = i + 1; j < 10; j++) {
      if (buffer_arr[i] > buffer_arr[j]) {
        temp = buffer_arr[i];
        buffer_arr[i] = buffer_arr[j];
        buffer_arr[j] = temp;
      }
    }
  }

  avgval = 0;
  for (int i = 2; i < 8; i++) avgval += buffer_arr[i];

  float volt = (float)avgval * 5.0 / 1024.0 / 6.0;
  ph_act = -5.70 * volt + calibration_value;
  return ph_act;
}

void readMics(float &co, float &ch4, float &c2h5oh, float &h2, float &nh3, float &no2) {
  co     = mics.getGasData(CO);
  ch4    = mics.getGasData(CH4);
  c2h5oh = mics.getGasData(C2H5OH);
  h2     = mics.getGasData(H2);
  nh3    = mics.getGasData(NH3);
  no2    = mics.getGasData(NO2);
}

// ============================================================
//                          SETUP
// ============================================================
void setup() {
  Serial.begin(115200);
  while (!Serial) { ; }

  // Basic pin modes
  pinMode(CO2_PWM_PIN, INPUT);
  pinMode(SOIL_PIN, INPUT);
  pinMode(PH_PIN, INPUT);

  // BMP3 SPI CS pin (even if I2C is used, safe to set)
  pinMode(SPI_CS_PIN, OUTPUT);
  spi_bmp3_cs_high();

  Serial.println("Initializing sensors...");
  delay(300);

  // ---- MICS init ----
  Serial.println("[1] MICS init...");
  if (!mics.begin()) {
    Serial.println("MICS not detected! Check wiring.");
  } else {
    if (mics.getPowerState() == SLEEP_MODE) {
      mics.wakeUpMode();
      Serial.println("MICS waking up...");
    }
    Serial.println("Warming up MICS...");
    while (!mics.warmUpTime(CALIBRATION_TIME)) {
      Serial.println(" ...warming");
      delay(1000);
    }
    Serial.println("MICS ready.");
  }

  // ---- BMP3 init ----
  Serial.println("[2] BMP3 init...");
  rslt = bmp3_interface_init(&dev);
  bmp3_check_rslt("bmp3_interface_init", rslt);

  rslt = bmp3_init(&dev);
  bmp3_check_rslt("bmp3_init", rslt);

  settings.int_settings.drdy_en = BMP3_ENABLE;
  settings.press_en = BMP3_ENABLE;
  settings.temp_en  = BMP3_ENABLE;

  settings.odr_filter.press_os = BMP3_OVERSAMPLING_2X;
  settings.odr_filter.temp_os  = BMP3_OVERSAMPLING_2X;
  settings.odr_filter.odr      = BMP3_ODR_100_HZ;

  settings_sel = BMP3_SEL_PRESS_EN | BMP3_SEL_TEMP_EN |
                 BMP3_SEL_PRESS_OS | BMP3_SEL_TEMP_OS |
                 BMP3_SEL_ODR | BMP3_SEL_DRDY_EN;

  rslt = bmp3_set_sensor_settings(settings_sel, &settings, &dev);
  bmp3_check_rslt("bmp3_set_sensor_settings", rslt);

  settings.op_mode = BMP3_MODE_NORMAL;
  rslt = bmp3_set_op_mode(&settings, &dev);
  bmp3_check_rslt("bmp3_set_op_mode", rslt);

  Serial.println("System ready.");
}

// ============================================================
//                           LOOP
// ============================================================
void loop() {
  // ---- BMP3 read (temperature + pressure) ----
  float bmp_temp = NAN;
  float bmp_press = NAN;

  rslt = bmp3_get_status(&status, &dev);
  // (optional) only print errors; avoids spamming
  if (rslt != BMP3_OK) bmp3_check_rslt("bmp3_get_status", rslt);

  if ((rslt == BMP3_OK) && (status.intr.drdy == BMP3_ENABLE)) {
    rslt = bmp3_get_sensor_data(BMP3_PRESS_TEMP, &data, &dev);
    if (rslt != BMP3_OK) bmp3_check_rslt("bmp3_get_sensor_data", rslt);

    // Clear drdy
    rslt = bmp3_get_status(&status, &dev);
    if (rslt != BMP3_OK) bmp3_check_rslt("bmp3_get_status(clear)", rslt);

    bmp_temp  = data.temperature;
    bmp_press = data.pressure;
  }

  // ---- MICS ----
  float co, ch4, c2h5oh, h2, nh3, no2;
  readMics(co, ch4, c2h5oh, h2, nh3, no2);

  // ---- Soil ----
  int soilRaw = analogRead(SOIL_PIN);
  int soilPercent = readSoilMoisturePercent(SOIL_PIN);

  // ---- pH ----
  float ph = readPH();

  // ---- CO2 ----
  float co2 = readCO2_PWM(CO2_PWM_PIN);

  // ---- Serial output (single-line, easy to log) ----
  Serial.print("CO: "); Serial.print(co);
  Serial.print(" | CH4: "); Serial.print(ch4);
  Serial.print(" | C2H5OH: "); Serial.print(c2h5oh);
  Serial.print(" | H2: "); Serial.print(h2);
  Serial.print(" | NH3: "); Serial.print(nh3);
  Serial.print(" | NO2: "); Serial.print(no2);

  Serial.print(" | Soil(%): "); Serial.print(soilPercent);
  Serial.print(" | SoilRaw: "); Serial.print(soilRaw);

  Serial.print(" | pH: "); Serial.print(ph, 2);

  Serial.print(" | CO2: "); Serial.print(co2); Serial.print(" ppm");

  Serial.print(" | BMP_T: "); 
  if (isnan(bmp_temp)) Serial.print("NA");
  else Serial.print(bmp_temp);

  Serial.print(" C | BMP_P: ");
  if (isnan(bmp_press)) Serial.print("NA");
  else Serial.print(bmp_press);

  Serial.println(" Pa");

  delay(500);
}
