/*  mMM test program
 *   Test various peripherals
 *   Open a serial terminal for menu
 *   Kevin Osborn
 */
#include <string.h>
#include <SPI.h>

#define PUMPPIN 9
#define SPEAKER 6
#define VALVE1  4
#define VALVE2  5
#define LED     13
#define BUTTON1 2
#define BUTTON2 3
#define SS 10
void speakerTest();
void GagePressureTest();
void blink();
void pwmPumpTest();
void binaryPumpTest();
void valveTest(int valve);
void menu();

 void setup() {
  Serial.begin(115200);
  pinMode(PUMPPIN,OUTPUT);
  pinMode(SPEAKER,OUTPUT);
  pinMode(VALVE1,OUTPUT);
  pinMode(VALVE2,OUTPUT);
  pinMode(LED,OUTPUT);

  speakerTest();
  menu();
  
  
}
void menu(){
  // print menu
  Serial.println("mmM test Peripherals");
  Serial.println("P -- Pump binary test");
  Serial.println("W -- Pump PWM test");
  Serial.println("1 -- Valve 1 test");
  Serial.println("2 -- Valve 2 test");
  Serial.println("S -- SpeakerTest");
  Serial.println("G -- Gauge Pressure Test");
  Serial.println("B -- pump, release, report pressures");
  Serial.println("h or ? -- this menu");
  
}
void valveTest(int valve){
  // Test valve(s)
  if (valve == VALVE1)
    Serial.println("Valve1 test");
  if (valve == VALVE2)
    Serial.println("Valve2 test");
  for(int i = 0 ; i < 10; i++){
  digitalWrite(valve,HIGH);
  delay(500);
  digitalWrite(valve,LOW);
  delay(500);
  }
}
void binaryPumpTest(long time){
    // Test pump
  Serial.println("Pump Full speed");
  digitalWrite(PUMPPIN, HIGH);
  delay(time);
  digitalWrite(PUMPPIN,LOW);
  blink();
}
void pwmPumpTest(){
    // PWM pump test
  Serial.println("Pump PWM");
  for (int i =80; i < 255; i++){
    analogWrite(PUMPPIN, i);
    Serial.println(i);
    delay(100);
  }
  digitalWrite(PUMPPIN,LOW);
  blink();
}
void pumpUntil (uint16_t pressure){
  digitalWrite(PUMPPIN,HIGH);
  while(ReadPressure() < pressure)
    delay(10);
  digitalWrite(PUMPPIN,LOW);
}
void GagePressureTest(){
  Serial.print("[\n");
  for (int i =0; i < 5000; i++){
    Serial.print(ReadPressure());
    Serial.print(",\n");
    delay(10);
    }
    Serial.print("]\n");
}

// read pressure with 10 ms delay
// and print in python array format until pressure
void ReadPressureUntil(uint16_t pressure){
    uint16_t reading;
    Serial.print("[\n");
    while ((reading = ReadPressure()) > pressure){
      Serial.print(reading);
      Serial.print(",\n");
      delay(10);
    }
    Serial.print("]\n");
    

}
uint16_t ReadPressure(){
  uint16_t reading;
  SPI.begin();
  SPI.setDataMode(SPI_MODE0);
  SPI.setClockDivider(SPI_CLOCK_DIV32); //  or 2,4,8,16,32,64,128
  digitalWrite(SS, LOW);
  SPI.transfer(255);
  reading =0;
  reading  |= SPI.transfer(255)<<8;
  reading |= SPI.transfer(255) &0x0ff;
  digitalWrite(SS, HIGH);
  return reading;
}
void speakerTest(){
   //Test speaker
  for (int i = 500; i < 2000; i+=100)
  {
    tone(SPEAKER,i,100);
    delay(100);
  }
}
void blink(){
  digitalWrite(LED,HIGH);
  delay(1000);
  digitalWrite(LED,LOW);
}
void bp_sim(){
  digitalWrite(VALVE1,HIGH); //close valve
  pumpUntil(12000);
  digitalWrite(VALVE1,LOW); //open valve
  ReadPressureUntil(2800);
  
}
void loop() {
  if (Serial.available()){
    char c = Serial.read();
    switch (c){
      case 'P':
      case 'p':
        binaryPumpTest(2000);
        break;
      case 'W':
      case 'w':
        pwmPumpTest();
        break;
      case 'B':
      case 'b':
        bp_sim();
        break;
      case 'S':
      case 's':
        speakerTest();
        break;
      case '1':
        valveTest(VALVE1);
        break;
      case '2':
        valveTest(VALVE2);
        break;
      case 'G':
      case 'g':
        GagePressureTest();
        break;
      case 'M':
      case '?':
      case 'm':
        menu();
        break;
      default:
        break;
     }
     menu();
  }
  if (digitalRead(BUTTON1))
  { 
    Serial.println("Button1 pressed");
    delay(200);
  }
  if (digitalRead(BUTTON2))
  { 
    Serial.println("Button2 pressed");
    delay(200);
  }
  

}
