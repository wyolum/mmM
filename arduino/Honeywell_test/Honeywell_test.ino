#include <Wire.h>

#define HONEYWELL_ADDR 0x49
void setup(){
  Serial.begin(115200);
  Serial.println("Honeywell_test");
  Wire.begin();
}

void read_flow(byte *where){
  short flow;
  
// Hi Res Sensirion start initiate read command
// end hi res start initaate read command
//  Wire.requestFrom(SENSIRION_ADDR_1, 2);
  Wire.requestFrom(HONEYWELL_ADDR, 2);
  if(Wire.available() == 2){
    where[1] = Wire.read(); 
    where[0] = Wire.read(); 
  }
  if(where[0] >> 6){
    Serial.println("status");
    read_flow(where);
  }
}

byte where[2];
uint16_t val;

void loop(){
  read_flow(where);
  val = (uint16_t)*where;
  Serial.println(val);
  delay(10);
}
