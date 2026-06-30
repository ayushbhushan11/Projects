#include "Arduino.h"
#include "Wire.h"
#include "SPI.h"

#include "bmp3.h"

#define ITERATION UINT8_C(100)
#define I2C_ADDRESS BMP3_ADDR_I2C_SEC
#define SPI_CS_PIN SS
#define USEIIC 1

uint8_t dev_addr;

void spi_bmp3_cs_high(void) {
  digitalWrite(SPI_CS_PIN, 1);
}
void spi_bmp3_cs_low(void) {
  digitalWrite(SPI_CS_PIN, 0);
}
/*!
 * Delay function 
 */
void bmp3_user_delay_us(uint32_t period, void *intf_ptr) {
  /* Wait for a period amount of microseconds. */
  delayMicroseconds(period);
}
/*!
 * I2C read function 
 */
BMP3_INTF_RET_TYPE bmp3_user_i2c_read(uint8_t reg_addr, uint8_t *reg_data, uint32_t len, void *intf_ptr) {

  /* Read from registers using I2C. Return 0 for a successful execution. */
  int i = 0;
  Wire.beginTransmission(I2C_ADDRESS);
  Wire.write(reg_addr);
  if (Wire.endTransmission() != 0) {
    return -1;
  }
  Wire.requestFrom((uint8_t)I2C_ADDRESS, (uint8_t)len);
  while (Wire.available()) {
    reg_data[i++] = Wire.read();
  }
  return 0;
}

/*!
 * I2C write function 
 */
BMP3_INTF_RET_TYPE bmp3_user_i2c_write(uint8_t reg_addr, uint8_t *reg_data, uint32_t len, void *intf_ptr) {
  /* Write to registers using I2C. Return 0 for a successful execution. */
  Wire.beginTransmission(I2C_ADDRESS);
  Wire.write(reg_addr);
  for (uint8_t i = 0; i < len; i++) {
    Wire.write(reg_data[i]);
  }
  Wire.endTransmission();
  return 0;
}

/*!
 * SPI read function 
 */
BMP3_INTF_RET_TYPE bmp3_user_spi_read(uint8_t reg_addr, uint8_t *reg_data, uint32_t len, void *intf_ptr) {
  /* Read from registers using SPI. Return 0 for a successful execution. */
  int8_t rslt = 0;
  spi_bmp3_cs_high();
  spi_bmp3_cs_low();
  SPI.transfer(reg_addr|0x80);
  for (uint8_t i = 0; i < len; i++) {
    reg_data[i] = SPI.transfer(0xFF);
  }
  spi_bmp3_cs_high();
  return rslt;
}

/*!
 * SPI write function 
 */
BMP3_INTF_RET_TYPE bmp3_user_spi_write(uint8_t reg_addr, uint8_t *reg_data, uint32_t len, void *intf_ptr) {
  /* Write to registers using SPI. Return 0 for a successful execution. */
  int8_t rslt = 0;

  spi_bmp3_cs_high();
  spi_bmp3_cs_low();
  SPI.transfer(reg_addr&0x7F);
  for(uint8_t i = 0; i < len; i++){
    SPI.transfer(reg_data[i]);
  }
  spi_bmp3_cs_high();
  return rslt;
}


BMP3_INTF_RET_TYPE bmp3_interface_init(struct bmp3_dev *bmp3) {
  int8_t rslt = BMP3_OK;

  if (bmp3 != NULL) {
    if (USEIIC) {
      bmp3->intf = BMP3_I2C_INTF;
    } else {
      bmp3->intf = BMP3_SPI_INTF;
    }
    /* Bus configuration : I2C */
    if (bmp3->intf == BMP3_I2C_INTF) {
      Wire.begin();
      Serial.print("I2C Interface\n");
      //bmp3_user_i2c_init();
      dev_addr = I2C_ADDRESS;
      bmp3->read = bmp3_user_i2c_read;
      bmp3->write = bmp3_user_i2c_write;
    }
    /* Bus configuration : SPI */
    else if (bmp3->intf == BMP3_SPI_INTF) {
      SPI.begin();
      Serial.print("SPI Interface\n");
      //bmp3_user_spi_init();
      dev_addr = 0;
      bmp3->read = bmp3_user_spi_read;
      bmp3->write = bmp3_user_spi_write;
    }

    bmp3->delay_us = bmp3_user_delay_us;
    bmp3->intf_ptr = &dev_addr;
  } else {
    rslt = BMP3_E_NULL_PTR;
  }

  return rslt;
}
void bmp3_check_rslt(const char api_name[], int8_t rslt) {
  switch (rslt) {
    case BMP3_OK:

      /* Do nothing */
      break;
    case BMP3_E_NULL_PTR:
      Serial.print("API:");Serial.print(api_name);Serial.print("Error:Null pointer;");Serial.println(rslt);
      break;
    case BMP3_E_COMM_FAIL:
      Serial.print("API:");Serial.print(api_name);Serial.print("Error:Communication failure;");Serial.println(rslt);
      break;
    case BMP3_E_INVALID_LEN:
      Serial.print("API:");Serial.print(api_name);Serial.print("Error:Incorrect length parameter;");Serial.println(rslt);
      break;
    case BMP3_E_DEV_NOT_FOUND:
      Serial.print("API:");Serial.print(api_name);Serial.print("Error:Device not found;");Serial.println(rslt);
      break;
    case BMP3_E_CONFIGURATION_ERR:
      Serial.print("API:");Serial.print(api_name);Serial.print("Error:Configuration Error;");Serial.println(rslt);
      break;
    case BMP3_W_SENSOR_NOT_ENABLED:
      Serial.print("API:");Serial.print(api_name);Serial.print("Error:Warning when Sensor not enabled;");Serial.println(rslt);
      break;
    case BMP3_W_INVALID_FIFO_REQ_FRAME_CNT:
      Serial.print("API:");Serial.print(api_name);Serial.print("Error:Warning when Fifo watermark level is not in limit;");Serial.println(rslt);
      break;
    default:
      Serial.print("API:");Serial.print(api_name);Serial.print("Error:Unknown error code;");Serial.println(rslt);
      break;
  }
}



int8_t rslt;
uint16_t settings_sel;
struct bmp3_dev dev;
struct bmp3_data data = { 0 };
struct bmp3_settings settings = { 0 };
struct bmp3_status status = { { 0 } };

void setup() {
  /* Interface reference is given as a parameter
    *         For I2C : BMP3_I2C_INTF
    *         For SPI : BMP3_SPI_INTF
    */
  
  
  pinMode(SPI_CS_PIN,OUTPUT);
  Serial.begin(115200);
  rslt = bmp3_interface_init(&dev);
  bmp3_check_rslt("bmp3_interface_init", rslt);

  rslt = bmp3_init(&dev);
  bmp3_check_rslt("bmp3_init", rslt);

  settings.int_settings.drdy_en = BMP3_ENABLE;
  settings.press_en = BMP3_ENABLE;
  settings.temp_en = BMP3_ENABLE;

  settings.odr_filter.press_os = BMP3_OVERSAMPLING_2X;
  settings.odr_filter.temp_os = BMP3_OVERSAMPLING_2X;
  settings.odr_filter.odr = BMP3_ODR_100_HZ;

  settings_sel = BMP3_SEL_PRESS_EN | BMP3_SEL_TEMP_EN | BMP3_SEL_PRESS_OS | BMP3_SEL_TEMP_OS | BMP3_SEL_ODR | BMP3_SEL_DRDY_EN;

  rslt = bmp3_set_sensor_settings(settings_sel, &settings, &dev);
  bmp3_check_rslt("bmp3_set_sensor_settings", rslt);

  settings.op_mode = BMP3_MODE_NORMAL;
  rslt = bmp3_set_op_mode(&settings, &dev);
  bmp3_check_rslt("bmp3_set_op_mode", rslt);
}
void loop() {
  rslt = bmp3_get_status(&status, &dev);
  bmp3_check_rslt("bmp3_get_status", rslt);

  /* Read temperature and pressure data iteratively based on data ready interrupt */
  if ((rslt == BMP3_OK) && (status.intr.drdy == BMP3_ENABLE)) {
    /*
    * First parameter indicates the type of data to be read
    * BMP3_PRESS_TEMP : To read pressure and temperature data
    * BMP3_TEMP       : To read only temperature data
    * BMP3_PRESS      : To read only pressure data
    */
    rslt = bmp3_get_sensor_data(BMP3_PRESS_TEMP, &data, &dev);
    bmp3_check_rslt("bmp3_get_sensor_data", rslt);

    /* NOTE : Read status register again to clear data ready interrupt status */
    rslt = bmp3_get_status(&status, &dev);
    bmp3_check_rslt("bmp3_get_status", rslt);

    Serial.print("T:");Serial.print(data.temperature);Serial.print(" deg C,P:");Serial.print(data.pressure);Serial.println(" Pa");

    //loop = loop + 1;
  }
  delay(500);
}
