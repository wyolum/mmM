#include <HardWire.h>
#define LIQ_PRESS_ADDR 120 
void setup() {
  Wire.begin();
  Serial.begin(115200);
  Serial.print("Ready to read");

}

int read_liquid_pressure(){
  Wire.requestFrom(LIQ_PRESS_ADDR,(byte)2);
  byte high_b, low_b;
  if (Wire.available() == 2){
    high_b = Wire.read();
    low_b = Wire.read();
  }
  return ( ((int)high_b <<8)  | (int) (low_b & 0x0ff));
}
void loop() {
  int liq_pressure;

  liq_pressure = read_liquid_pressure();
  Serial.println(liq_pressure);
  delay(10);
}

