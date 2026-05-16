/*
 * mmMControl3.ino
 * Based on mmMControl2 — adds analog PWM pump control.
 * 
 * Change from mmMControl2:
 *   control_pump() now uses analogWrite(PUMP_PIN, rate) so that
 *   command[3] (0-255) sets pump speed, not just on/off.
 *   Pin 9 (PUMP_PIN) supports hardware PWM on ATmega328P (Timer 1).
 *   All other behaviour is identical to mmMControl2.
 */

#include "uControl.h"
#include <Wire.h>
#include <SoftwareSerial.h>
#include <SPI.h>

#define SENSIRION_ADDR_1 64
#define SENSIRION_ADDR_2 1
#define HONEYWELL_ADDR 0x49

void Serial_flush_input(){
  while(Serial.available()){
    Serial.read();
  }
}

void send_msg(byte *dat, byte n){
  byte cksum = 0;
  for(byte i=0; i < n; i++){
    cksum += dat[i];
  }
  Serial.write(dat, n);
  Serial.write(cksum);
}

void error(byte error_code){
  while(1){
    for(int ii=0; ii < 10; ii++){
      Serial.print("ERROR:");
      Serial.println(error_code, DEC);
      for(byte i=0; i < error_code; i++){
        digitalWrite(LED, HIGH);
        delay(200);
        digitalWrite(LED, LOW);
        delay(200);
      }
      delay(600);
    }
  }
}

/*
 * Pump at given rate 0-255.
 * 0   = off
 * 1-255 = analogWrite PWM duty cycle (pin 9 = Timer1, hardware PWM)
 * 
 * This replaces the boolean digitalWrite from mmMControl2.
 */
void control_pump(int rate){
  if(rate <= 0){
    analogWrite(PUMP_PIN, 0);
    digitalWrite(PUMP_PIN, LOW);   // ensure fully off
  }
  else{
    analogWrite(PUMP_PIN, constrain(rate, 1, 255));
  }
}

void pump_on(){
  control_pump(255);
}
void pump_off(){
  control_pump(0);
}

void control_valve(int state){
  if (!state & 0x80) return;
  if((state & 0x01) == VALVE_OPEN){
    valve_is_closed = false;
    pressure_start = -1;
    digitalWrite(VALVE1_PIN, LOW);
  }
  else{
    valve_is_closed = true;
    pressure_start = millis();
    digitalWrite(VALVE1_PIN, HIGH);
  }
  if(((state & 0x02)>>1) == VALVE_OPEN){
    pressure_start = -1;
    digitalWrite(VALVE2_PIN, LOW);
  }
  else{
    pressure_start = millis();
    digitalWrite(VALVE2_PIN, HIGH);
  }
}
void valves_close(){
  control_valve(0x80);
}
void valves_open(){
  control_valve(0x83);
}

bool set_next_sample(unsigned long now_ms){
  unsigned int current = millis();
  next_sample_ms = now_ms + interval_ms;
  if(next_sample_ms < current){
    next_sample_ms = current + interval_ms;
  }
  if(next_sample_ms < now_ms){
    error(ROLLOVER_ERROR);
  }
}
boolean set_next_sample(){
  set_next_sample(next_sample_ms);
}
bool lr_set_next_sample(unsigned long now_ms){
  unsigned int current = millis();
  lr_next_sample_ms = now_ms + lr_interval_ms;
  if(lr_next_sample_ms < current){
    lr_next_sample_ms = current + lr_interval_ms;
  }
  if(lr_next_sample_ms < now_ms){
    error(ROLLOVER_ERROR);
  }
}

void start_sampling(unsigned long __interval_ms){
  unsigned long now_ms = millis();
  if(__interval_ms != interval_ms){
    interval_ms = __interval_ms;
    if(__interval_ms > 0){
      sampling = true;
      set_next_sample(now_ms);
      lr_set_next_sample(now_ms);
    }
    else{
      sampling = false;
    }
  }
}

void read_cuff(byte *where){
  digitalWrite(SS, LOW);
  SPI.transfer(255);
  where[1] = SPI.transfer(255);
  where[0] = SPI.transfer(255);
  digitalWrite(SS, HIGH);
}

void read_amb_temp(byte *where){
#ifdef TEMP_STS21
  Wire.requestFrom(STS_ADDR, (byte)3);
  if(Wire.available() > 2){
    where[1] = Wire.read();
    where[0] = Wire.read();
  }
#else
  where[1] = 0;
  where[0] = 20;
#endif
}

void read_amb_pressure(byte *where){
#ifdef AMB_PRESSURE
  Wire.requestFrom(AMB_PRESS_ADDR, (byte)2);
  if(Wire.available() == 2){
    where[1] = Wire.read();
    where[0] = Wire.read();
  }
#else
  where[1] = 0;
  where[0] = 0;
#endif
}

void read_liquid_pressure(byte *where){
  Wire.requestFrom(LIQ_PRESS_ADDR, (byte)2);
  if(Wire.available() == 2){
    where[1] = Wire.read();
    where[0] = Wire.read();
  }
}

void read_flow(uint8_t *where){
  short flow;
  uint8_t last[2];
  last[0] = where[0];
  last[1] = where[1];
  Wire.requestFrom(HONEYWELL_ADDR, 2);
  if(Wire.available() == 2){
    where[1] = Wire.read();
    where[0] = Wire.read();
  }
  if((where[1] & 0xC0) || (where[0] == 0 && where[1] == 0)){
    where[0] = last[0];
    where[1] = last[1];
  }
}

void read_pulse(byte *where){
  cli();
  *(unsigned short*)where = analogRead(PULSE_PIN);
  sei();
}

void take_sample(){
  unsigned short *pulse_sensor = (unsigned short*)(hirate_data + 9);
  unsigned long now_ms = millis();
  if(sampling && (next_sample_ms <= now_ms)){
    set_next_sample();
    hirate_data[0] = MEASUREMENTS_PID;
    *(unsigned long *)(hirate_data + 1) = now_ms;
    read_cuff(hirate_data + 5);
    read_flow(hirate_data + 7);
#ifdef LIQUID_PRESSURE_SENSOR
    read_liquid_pressure(hirate_data + 9);
#endif
    send_msg(hirate_data, MEASUREMENTS_LEN);
  }
}

boolean serial_interact(){
  byte pos = 0;
  byte cksum = 0;
  boolean out = false;
  byte n_try = 0;

  if(Serial.available()){
    while(Serial.available() < COMMAND_LENGTH && n_try++ < 10){
      delay(1);
    }
    if(Serial.available() >= COMMAND_LENGTH){
      if(COMMAND_START == Serial.read() && COMMAND_START == Serial.read()){
        out = true;
        for(byte ii=2; ii < COMMAND_LENGTH; ii++){
          char c = Serial.read();
          command[pos] = c;
          if(pos != 0){
            cksum += command[pos];
            cksum %= 256;
          }
          pos++;
        }
        if((byte)command[0] == (byte)cksum){
          if(command[1] == 1){
            bpc_setup();
            command[1] = 2;
          }
          start_sampling(SAMPLE_INTERVAL_STEP_MS * command[2]);

          /* command[3] is now 0-255 pump PWM rate, not boolean */
          control_pump((int)(byte)command[3]);

          control_valve((int)command[4]);

          if(command[5]){
            if((command[5] >> 0) & 1){
              status_msg[3] = 0;
              *(unsigned short*)(status_msg + 1) = *(unsigned short*)(hirate_data + 5);
              send_msg(status_msg, 4);
            }
            if((command[5] >> 1) & 1){
              status_msg[3] = 1;
              *(unsigned short*)(status_msg + 1) = *(unsigned short*)(hirate_data + 7);
              send_msg(status_msg, 4);
            }
            if((command[5] >> 2) & 1){
              status_msg[3] = 2;
              *(unsigned short*)(status_msg + 1) = *(unsigned short*)(hirate_data + 9);
              send_msg(status_msg, 4);
            }
            if((command[5] >> 3) & 1){
              status_msg[3] = 3;
              read_amb_pressure(status_msg + 1);
              send_msg(status_msg, 4);
            }
            if((command[5] >> 4) & 1){
              status_msg[3] = 4;
              read_amb_temp(status_msg + 1);
              send_msg(status_msg, 4);
            }
            if((command[5] >> 5) & 1){
              status_msg[3] = 5;
              status_msg[1] = *pump_state_p;
              status_msg[2] = 0;
              send_msg(status_msg, 4);
            }
            if((command[5] >> 6) & 1){
              status_msg[3] = 6;
              status_msg[1] = (*valve_state_p) & 0x7f;
              status_msg[2] = 0;
              send_msg(status_msg, 4);
            }
            if((command[5] >> 7) & 1){
              status_msg[3] = 7;
              status_msg[1] = interval_ms;
              status_msg[2] = 0;
              send_msg(status_msg, 4);
            }
          }
        }
        else{
          short_msg[1] = 'C';
          short_msg[2] = 'C';
          send_msg(short_msg, 3);
          Serial_flush_input();
        }
      }
      else{
        short_msg[1] = 'C';
        short_msg[2] = 'S';
        send_msg(short_msg, 3);
        Serial_flush_input();
      }
    }
    else{
      short_msg[1] = 'C';
      short_msg[2] = 'L';
      send_msg(short_msg, 3);
      short_msg[1] = 'C';
      short_msg[2] = Serial.available();
      send_msg(short_msg, 3);
      while(Serial.available()){
        Serial.read();
      }
      Serial_flush_input();
    }
  }
  return out;
}

void bpc_setup(){
  Flow_cursor = 0;
  Flow_last_end = 0;

  pinMode(PUMP_PIN, OUTPUT);
  pinMode(VALVE1_PIN, OUTPUT);
  pinMode(VALVE2_PIN, OUTPUT);
  valves_open();
  pump_off();

#ifdef SERIAL_FLOW_SENSOR
  Flow_serial.begin(19200);
  if(!Flow_run_command("s\r\n", FLOW_MAX_TRY)){
    short_msg[1] = 'F'; short_msg[2] = 's'; send_msg(short_msg, 3);
  }
  if(!Flow_run_command("mod=f\r\n", FLOW_MAX_TRY)){
    short_msg[1] = 'F'; short_msg[2] = 'm'; send_msg(short_msg, 3);
  }
  if(!Flow_run_command("res=5\r\n", FLOW_MAX_TRY)){
    short_msg[1] = 'F'; short_msg[2] = 'r'; send_msg(short_msg, 3);
  }
  if(!Flow_run_command("go\r\n", FLOW_MAX_TRY)){
    short_msg[1] = 'F'; short_msg[2] = 'g'; send_msg(short_msg, 3);
  }
#endif

  Wire.begin();
#ifdef SENSIRION
  Wire.beginTransmission(SENSIRION_ADDR_1);
  Wire.write(0x10);
  Wire.write(0x00);
  Wire.endTransmission();
#endif
  valves_close();
#ifdef TEMPSTS21
  Wire.beginTransmission(STS_ADDR);
  Wire.write(STS_HOLD_MASTER);
  Wire.endTransmission();
#endif

  SPI.begin();
  SPI.setDataMode(SPI_MODE0);
  SPI.setClockDivider(SPI_CLOCK_DIV32);

  start_sampling(SAMPLE_INTERVAL_STEP_MS);
}

int Flow_read();
void Flow_convert();

void setup(){
  Serial.begin(BAUDRATE);
  bpc_setup();
  short_msg[1] = 'R';
  short_msg[2] = '!';
  send_msg(short_msg, 3);
}

void loop(){
  loop_count++;

  if(*cuff_pressure_p > CUFF_TOLL){
    abort(CUFF_PRESSURE_ERROR);
  }

  if(sampling){
    take_sample();
  }
  if(pressure_start > 0){
    if((millis() - pressure_start) > MAX_TEST_TIME){
      abort(MAX_TEST_TIME_ERROR);
    }
  }

  Flow_convert();
  Flow_read();

  if(serial_interact()){
  }
}

void abort(byte code){
  valves_open();
  pump_off();
  command[1] = 0;
  short_msg[1] = 'A';
  short_msg[2] = code;
  send_msg(short_msg, 3);
  while(command[1] == 0){
    serial_interact();
    send_msg(short_msg, 3);
  }
}

#ifdef FLOW_SENSOR
bool Flow_run_command(char *cmd, byte maxtry){
  byte read_bytes = 65;
  byte bytes_read = 0;
  int tries = 0;
  char c1 = (char)0;
  char c2 = (char)0;
  while(Flow_serial.available() && (bytes_read++ < read_bytes)){
    Flow_serial.read();
  }
  bytes_read = 0;
  Flow_serial.write(cmd);
  while(((c1 != 'O') || (c2 != 'K')) && (tries++ < maxtry)){
    Flow_serial.write(cmd);
    delay(20);
    while(Flow_serial.available() &&
          ((c1 != 'O') || (c2 != 'K')) &&
          (bytes_read++ < read_bytes)){
      c1 = c2;
      c2 = Flow_serial.read();
    }
  }
  if((c1 == 'O') && (c2 == 'K')){
    short_msg[1] = c1;
    short_msg[2] = c2;
    send_msg(short_msg, 3);
  }
  return (c1 == 'O') && (c2 == 'K');
}
#endif

int Flow_read(){
  int out = 0;
#ifdef FLOW_SENSOR
  while(Flow_serial.available()){
    Flow_msg[Flow_cursor++] = Flow_serial.read();
    Flow_cursor %= FLOW_MSG_LEN;
    out++;
  }
#else
  for(int i = 0; i < 2; i++){
    Flow_msg[Flow_cursor++] = 0;
    Flow_cursor %= FLOW_MSG_LEN;
    out++;
  }
#endif
  return Flow_cursor;
}

void Flow_convert(){
  if(Flow_last_end > Flow_cursor){
    for(int i = 0; i < Flow_cursor; i++){
      Flow_msg[FLOW_MSG_LEN - Flow_last_end + i] = Flow_msg[i];
    }
    for(int i = 0; i < FLOW_MSG_LEN - Flow_last_end; i++){
      Flow_msg[i] = Flow_msg[Flow_last_end + i];
    }
    Flow_cursor += FLOW_MSG_LEN - Flow_last_end;
    Flow_last_end = 0;
  }
  for(int i = Flow_last_end; i < Flow_cursor - 3; i++){
    if(Flow_msg[i] == 0x7F && Flow_msg[i + 1] == 0x7F){
      Flow_rate[0] = Flow_msg[i + 2];
      Flow_rate[1] = Flow_msg[i + 3];
    }
    Flow_last_end++;
  }
}
