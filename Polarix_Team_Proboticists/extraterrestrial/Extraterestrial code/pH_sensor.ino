// ---------- pH sensor variables ----------
float calibration_value = 28.8;
int buffer_arr[10], temp;
unsigned long int avgval;
float ph_act;

void setup()
{
  Serial.begin(9600);
}

void loop()
{
  // ---------- Read analog values ----------
  for (int i = 0; i < 10; i++) {
    buffer_arr[i] = analogRead(A0);
    delay(30);
  }

  // ---------- Sort readings ----------
  for (int i = 0; i < 9; i++) {
    for (int j = i + 1; j < 10; j++) {
      if (buffer_arr[i] > buffer_arr[j]) {
        temp = buffer_arr[i];
        buffer_arr[i] = buffer_arr[j];
        buffer_arr[j] = temp;
      }
    }
  }

  // ---------- Average middle values ----------
  avgval = 0;
  for (int i = 2; i < 8; i++)
    avgval += buffer_arr[i];

  // ---------- Voltage & pH calculation ----------
  float volt = (float)avgval * 5.0 / 1024.0 / 6.0;
  ph_act = -5.70 * volt + calibration_value;

  // ---------- Serial output ----------
  Serial.print("pH Value: ");
  Serial.println(ph_act, 2);

  delay(1000); // measurement interval
}
