
// Zephyr sensor reading
// note: requires external pullups. 1.5K seem to work well with breadboard


#include <Wire.h>
#ifndef cbi
#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#endif

#define SENSIRION_ADDR 64
#define SENSIRION_READ_FLOW 0x1000
#define SENSIRION_READ_TEMP 0x1001
#define SENSIRION_SCALE_FACTOR_F 140
#define SENSIRION_SCALE_FACTOR_T 100
#define SENSIRION_OFFSET_F 32000
#define SENSIRION_OFFSET_T 20000

void probe_I2C();
void setup()
{
  Wire.begin();        // join i2c bus (address optional for master)
  Serial.begin(115200);  // start serial for output
  // probe_I2C();
  Wire.beginTransmission(SENSIRION_ADDR);
  Wire.write(0x10);
  Wire.write(0x00);
  Wire.endTransmission();
}
float getFlow(){
  float flow;
  int count;

  Wire.requestFrom(SENSIRION_ADDR, 2);    // request 6 bytes from slave device #2
  count = Wire.read()<<8;
  count |= Wire.read();
  return (count - SENSIRION_OFFSET_F) / float(SENSIRION_SCALE_FACTOR_F);

}
float getTemp(){
  Wire.beginTransmission(SENSIRION_ADDR);
  Wire.write(0x10);
  Wire.write(0x01);
  Wire.endTransmission();

  Wire.requestFrom(SENSIRION_ADDR, 2);    // request 6 bytes from slave device #2
  int count = Wire.read()<<8;
  count |= Wire.read();
  return count;
}
int loop_counter = 0;
void loop()
{
  float value = getFlow();
  //Serial.print(loop_counter++);
  //Serial.print(" ");
  Serial.print(value);
  Serial.println(" ");

 /* while(Wire.available())    // slave may send less than requested
  { 
    char c = Wire.read(); // receive a byte as character
    Serial.print(c,HEX);         // print the character
  }
  */

  delay(5);
}
void probe_I2C(){
  Serial.println("I2C Probe");
  int count = 0;
  for (byte i = 1; i < 120; i++){
    Wire.beginTransmission (i);
    if (Wire.endTransmission () == 0){
      Serial.print ("Found address: ");
      Serial.print (i, DEC);
      Serial.print (" (0x");
      Serial.print (i, HEX);
      Serial.println (")");
      count++;
      delay (1);  // maybe unneeded?
    } // end of good response
  } // end of for loop
  Serial.println ("Done.");
  Serial.print ("Found ");
  Serial.print (count, DEC);
  Serial.println (" device(s).");
}  // end of setup
