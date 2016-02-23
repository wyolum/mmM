/*  mMM test program
 *   Test various peripherals
 *   Open a serial terminal for menu
 *   Kevin Osborn
 */
#include <string.h>
#define PUMPPIN 9
#define SPEAKER 6
#define VALVE1  4
#define VALVE2  5
#define LED     13
#define BUTTON1 2
#define BUTTON2 3
void speakerTest();
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
void binaryPumpTest(){
    // Test pump
  Serial.println("Pump Full speed");
  digitalWrite(PUMPPIN, HIGH);
  delay(2000);
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
void loop() {
  if (Serial.available()){
    char c = Serial.read();
    switch (c){
      case 'P':
        binaryPumpTest();
        break;
      case 'W':
        pwmPumpTest();
        break;
      case 'S':
        speakerTest();
        break;
      case '1':
        valveTest(VALVE1);
        break;
      case '2':
        valveTest(VALVE2);
        break;
      case 'M':
      case '?':
      case 'm':
        menu();
        break;
      default:
        break;
    }
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
