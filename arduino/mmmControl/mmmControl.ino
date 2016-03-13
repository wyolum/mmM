#include "uControl.h"
#include <Wire.h>
#include <SoftwareSerial.h>
#include <SPI.h>


/*
 * Flush and discard all serial input
 */
void Serial_flush_input(){
  while(Serial.available()){
    Serial.read();
  }
}

/*
 * compute check sum, send data
 * 
 * dat -- pointer to message data
 *   n -- number of message bytes (not including check sum)
 */
void send_msg(byte *dat, byte n){
  byte cksum = 0;
  for(byte i=0; i < n; i++){
    cksum += dat[i];
  }
  Serial.write(dat, n);
  Serial.write(cksum);
}

/*
 * stop exectution until next reset
 */
void error(byte error_code){
  while(1){
    for(int ii=0; ii < 10; ii++){
      Serial.print("ERROR:");// TODO: FORMAT ERROR STATUS PACKET
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
 * Pump at given rate for duration in miliseconds.
 * rate = 0: off
 */
void control_pump(int rate){
  if(rate > 0){
    digitalWrite(PUMP_PIN, HIGH);
  }
  else{
    digitalWrite(PUMP_PIN, LOW);
  }
}
void pump_on(){
  control_pump(1);
}
void pump_off(){
  control_pump(0);
}

/*
 * Open valve
 * full closed 0 <= dc <= 1(full open)
 * State for two valves is set in bits 0,1
 * enable is bit 7. If bit 7 is set, control both valves
 */
void control_valve(int  state){
  if (!state &0x80) return;
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
    digitalWrite(VALVE1_PIN, LOW);
  }
  else{
    pressure_start = millis();
    digitalWrite(VALVE1_PIN, HIGH);
  }
}
void valves_close(){
  control_valve(0x80);
}
void valves_open(){
  control_valve(0x83);
}

/*
 * Start sampling pressure sensor at given rate (20 Hz max)
 */
bool set_next_sample(unsigned long now_ms){
  unsigned int current = millis();
  next_sample_ms = now_ms + interval_ms;
  if(next_sample_ms < current){
    next_sample_ms = current + interval_ms;
  }
  if(next_sample_ms < now_ms){
    // millis() rollover!!! Should never have to worry.  Pi should reset between runs.
    // taked 49 days to roll over
    error(ROLLOVER_ERROR);
  }
}
boolean set_next_sample(){
  set_next_sample(next_sample_ms);
}
/*
 * Set next sample time for low rate data amb temp and pressure sensor
 */
bool lr_set_next_sample(unsigned long now_ms){
  unsigned int current = millis();
  lr_next_sample_ms = now_ms + lr_interval_ms;
  if(lr_next_sample_ms < current){
    lr_next_sample_ms = current + lr_interval_ms;
  }
  if(lr_next_sample_ms < now_ms){
    // millis() rollover!!! Should never have to worry.  Pi should reset between runs.
    // taked 49 days to roll over
    error(ROLLOVER_ERROR);
  }
}

void start_sampling(unsigned long __interval_ms){
  unsigned long now_ms = millis();
  if(__interval_ms != interval_ms){
    
    // Serial << "Start sampling" << __interval_ms << "\n";
    interval_ms = __interval_ms;
    if(__interval_ms > 0){
#ifdef FLOW_METER
      if(!Flow_serial.available()){
	if(!Flow_run_command("go\n", FLOW_MAX_TRY)){
	  short_msg[1] = 'F';
	  short_msg[2] = 'g';
	}
	else{
	  short_msg[1] = 'f';
	  short_msg[2] = Flow_serial.available();
	}
	send_msg(short_msg, 3);
      }
#else
// pretend there's flow data available
 short_msg[1] = 'f';
 short_msg[2] = 1;
 send_msg(short_msg, 3);
#endif
 

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
    where[0] = 20; //20 c room temp?
#endif
}

void read_amb_pressure(byte *where){
#ifdef AMB_PRESSURE
  Wire.requestFrom(AMB_PRESS_ADDR, (byte)2);
  if(Wire.available() == 2){
    where[1] = Wire.read();
    where[0] =  Wire.read();
  }
#else
  where [1] = 0;
  where [0] = 0;
#endif
}

void read_flow(byte *where){
  byte n_flow;
  short flow;

  where[0] = Flow_rate[1];
  where[1] = Flow_rate[0];
#ifdef NOTDEFINED // DBG Message
  short_msg[1] = 'O';
  short_msg[2] = where[0];
  send_msg(short_msg, 3);
  short_msg[1] = 'T';
  short_msg[2] = where[1];
  send_msg(short_msg, 3);
#endif
  /*-- MOCK UP ------------------------------------------------------------------------------*/
  
  // read from serial
  // *(unsigned short*)(where) = flow_rate;
  /*-- MOCK UP ------------------------------------------------------------------------------*/
  
}

void read_pulse(byte *where){
  cli();
  *(unsigned short*)where = analogRead(PULSE_PIN);
  sei();
}

void take_sample(){
  /*
    hirate data format
	  /*
	    byte#    purpose
	    0 -- MEASUREMENTS_PID
	    1 -- MILLISECS 0
	    2 -- MILLISECS 1
	    3 -- MILLISECS 2
	    4 -- MILLISECS 3
	    5 -- CUFF 0
	    6 -- CUFF 1
	    7 -- FLOW 0
	    8 -- FLOW 1
            9 -- PULSE 0
           10 -- PULSE 1
  */
  unsigned short *pulse_sensor = (unsigned short*)(hirate_data + 9);
  unsigned long now_ms = millis();
  if(sampling && (next_sample_ms <= now_ms)){
    set_next_sample();
    hirate_data[0] = MEASUREMENTS_PID;
    
    *(unsigned long *)(hirate_data + 1) = now_ms;
    
    // read pressure
    read_cuff(hirate_data + 5);
    
    // read flow
    read_flow(hirate_data + 7);

    // read pulse sensor
    read_pulse(hirate_data + 9);
    
    // send of hirate data
    send_msg(hirate_data, MEASUREMENTS_LEN);
  }
#ifdef NOT_DEFINED
  // not taking hirate samples can we take a low rate sample?
  if(valve_is_closed && sampling && 
     (lr_next_sample_ms <= now_ms) && // is it time for next lorate sample?
     (next_sample_ms  + 1 > now_ms)){ // 1 ms margin for low pri low rate data
    lr_set_next_sample(now_ms + lr_interval_ms);

    lorate_data[0] = LORATE_MEASUREMENTS_PID;
    *(unsigned long *)(lorate_data + 1) = now_ms;
    read_amb_pressure(lorate_data + 5);
    read_amb_temp(lorate_data + 7);
    send_msg(lorate_data, LORATE_MEASUREMENTS_LEN);
  }
#endif
}

/*
 * read serial stream into command buffer.  
 * return true if valid command is sent
 */

boolean serial_interact(){
  byte pos = 0;
  byte cksum = 0;
  boolean out = false;
  byte n_try = 0;

  if(Serial.available()){
    while(Serial.available() < COMMAND_LENGTH && n_try++ < 10){
      delay(1);
    }
    // delayMicroseconds(500); // wait for rest of message (BUG ALERT!!!)
    // take_sample();

    if(Serial.available() >= COMMAND_LENGTH){
      if(COMMAND_START == Serial.read() && COMMAND_START == Serial.read()){
	out = true; // new data
	for(byte ii=2; ii < COMMAND_LENGTH; ii++){
	  char c = Serial.read();
	  command[pos] = c;
	  if(pos != 0){
	    cksum += command[pos];
	    cksum %= 256;
	    /* 
	       Serial.print(command[pos], DEC);
	       Serial.print(":");
	       Serial.print(cksum, DEC);
	       Serial.print(",");
	    */
	  }
	  else{
	    /*
	      Serial.print(command[pos], DEC);
	      Serial.print("!!");
	    */
	  }
	  pos++;
	}
	if((byte)command[0] == (byte)cksum){ 
	  //  new data is valid
	  /*
	    byte#    purpose
	    0 -- 0x7F COMMAND_START
	    1 -- 0x7F COMMAND_START
	    2 -- checksum
	    3 -- initialize
	    4 -- sample interval
	    5 -- pump control
	    6 -- valve control
	    7 -- status request
	    8 -- \n COMMAND_END
	  */
	  if(command[1] == 1){ // Initialzation Command
	    bpc_setup();
	    command[1] = 2; // Set to initialized
	  }
	  start_sampling(SAMPLE_INTERVAL_STEP_MS * command[2]); // Sampling interval
	  // // Echo sample interval?
	  // short_msg[1] = 'S';
	  // short_msg[2] = interval_ms;
	  // send_msg(short_msg, 3);
	
	  control_pump((int)command[3]);
	  control_valve((int)command[4]);
	
	  if(command[5]){ // status
	    if((command[5] >> 0) & 1){
	      // CUFF
	      status_msg[3] = 0;
	      *(unsigned short*)(status_msg + 1) = *(unsigned short*)(hirate_data + 5);
	      send_msg(status_msg, 4);
	    }
	    if((command[5] >> 1) & 1){
	      // FLOW
	      status_msg[3] = 1;
	      *(unsigned short*)(status_msg + 1) = *(unsigned short*)(hirate_data + 7);
	      send_msg(status_msg, 4);
	    }
	    if((command[5] >> 2) & 1){
	      // PULSE
	      status_msg[3] = 2;
	      *(unsigned short*)(status_msg + 1) = *(unsigned short*)(hirate_data + 9);
	      send_msg(status_msg, 4);
	    }
	    if((command[5] >> 3) & 1){
	      // AMB PRESSURE
	      status_msg[3] = 3;
	      read_amb_pressure(status_msg + 1);
	      send_msg(status_msg, 4);
	    }
	    if((command[5] >> 4) & 1){
	      // AMB TEMP
	      status_msg[3] = 4;
	      read_amb_temp(status_msg + 1);
	      send_msg(status_msg, 4);
	    }
	    if((command[5] >> 5) & 1){
	      // PUMP
	      status_msg[3] = 5;
	      status_msg[1] = *pump_state_p;
	      status_msg[2] = 0;
	      send_msg(status_msg, 4);
	    }
	    if((command[5] >> 6) & 1){
	      // VALVE
	      status_msg[3] = 6;
	      status_msg[1] = (*valve_state_p)&0x7f;
	      status_msg[2] = 0;
	      send_msg(status_msg, 4);
	    }
	    if((command[5] >> 7) & 1){
	      // sample interval ms
	      status_msg[3] = 7;
	      status_msg[1] = interval_ms;
	      status_msg[2] = 0;
	      send_msg(status_msg, 4);
	    }
	  }
	}
	else{ // got new data but cksum was wrong
	  short_msg[1] = 'C'; // command 
	  short_msg[2] = 'C'; // check sum
	  send_msg(short_msg, 3);
	  Serial_flush_input();
	}
      }
      else{ // got new data but start of command was wrong
	short_msg[1] = 'C'; // command
	short_msg[2] = 'S'; // start
	send_msg(short_msg, 3);
	Serial_flush_input();
      }
    }
    else{
      short_msg[1] = 'C'; // command 
      short_msg[2] = 'L'; // length
      send_msg(short_msg, 3);
      short_msg[1] = 'C'; // command 
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
  // configure pins
  Flow_cursor=0;
  Flow_last_end = 0;
  
  pinMode(PUMP_PIN, OUTPUT);
  pinMode(VALVE1_PIN, OUTPUT);
  pinMode(VALVE2_PIN, OUTPUT);
  // open valve as audio feed back
  valves_open();
  
  // turn off pump
  pump_off();

#ifdef FLOW_SENSOR
// start flow sensor serial
  Flow_serial.begin(19200);

  // stop readings
  if(!Flow_run_command("s\r\n", FLOW_MAX_TRY)){
    short_msg[1] = 'F';
    short_msg[2] = 's';
    send_msg(short_msg, 3);    
  }
    
  // get flow readings
  if(!Flow_run_command("mod=f\r\n", FLOW_MAX_TRY)){
    short_msg[1] = 'F';
    short_msg[2] = 'm';
    send_msg(short_msg, 3);    
  } 
  //  set resolution, res=4==> 12.5 Hz res=5 ==> rate=6.25 Hz res=7 ==> rate ~1.56 Hz
  if(!Flow_run_command("res=5\r\n", FLOW_MAX_TRY)){
    short_msg[1] = 'F';
    short_msg[2] = 'r';
    send_msg(short_msg, 3);    
  } 
  // start measurements
  if(!Flow_run_command("go\r\n", FLOW_MAX_TRY)){
    short_msg[1] = 'F';
    short_msg[2] = 'g';
    send_msg(short_msg, 3);    
  } 
 #endif   
  // Serial.println("bpc_setup() flow ready");
  // start I2C
  Wire.begin();
  valves_close();
 #ifdef TEMPSTS21 
  // start STS21 temperature sensor
  Wire.beginTransmission(STS_ADDR);
  Wire.write(STS_HOLD_MASTER); // option: STS_NOHOLD_MASTER
  Wire.endTransmission();
#endif
  // start SPI for gage pressure
  SPI.begin();
  SPI.setDataMode(SPI_MODE0);
  SPI.setClockDivider(SPI_CLOCK_DIV32); //  or 2,4,8,16,32,64,128
 
  // start sampling at max rate
  start_sampling(SAMPLE_INTERVAL_STEP_MS);
}
void Flow_convert();
int Flow_read();
void setup(){
  // open serial stream
  Serial.begin(BAUDRATE);
  // Serial.println("uControl");
  bpc_setup();
  // toggle valve
  // Serial.println("ready");
  short_msg[1] = 'R'; // code for ready
  short_msg[2] = '!';
  send_msg(short_msg, 3);
}

#define SERIAL
void loop(){
  loop_count++;

  if(*cuff_pressure_p > CUFF_TOLL){
    abort(CUFF_PRESSURE_ERROR);
  }

  // take and send samples
  if(sampling){
    take_sample();
  }
  if(pressure_start > 0){
    if((millis() - pressure_start) > MAX_TEST_TIME){
      abort(MAX_TEST_TIME_ERROR);
    }
  }

  // Do these things last.  They can mess up timing

 // Serial.println("loop()");
  // Flow_run_command("go\n");
  Flow_convert();
  Flow_read();
  // return;
  // check for new serial commands
  if(serial_interact()){
  }
}

void abort(byte code){
  valves_open();
  pump_off();
  
  command[1] = 0; // go to un initialized state
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
    Flow_serial.read(); // flush data stream
  }

  bytes_read = 0; // reset bytes read

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
#endif //FLOW_SENSOR
int Flow_read(){
  int out, i;
  char c, two[2];

  out = 0;
#ifdef FLOW_SENSOR
  while(Flow_serial.available()){
    Flow_msg[Flow_cursor++] = Flow_serial.read();
    Flow_cursor %= FLOW_MSG_LEN;
    out += 1;
  }
#else
  for (int i =0; i < 2; i++){
    Flow_msg[Flow_cursor++] = 0; // fake flow reading
    Flow_cursor %= FLOW_MSG_LEN;
    out += 1;
  }
#endif
#ifdef NOTDEFINED // DBG message
    short_msg[1] = 'C';
    short_msg[2] = Flow_msg[Flow_cursor - 1];
    send_msg(short_msg, 3);
#endif

  if(out){
    // short_msg[1] = 'F';
    // short_msg[2] = out;
    // send_msg(short_msg, 3);
  }
  return Flow_cursor;
}

void Flow_convert(){
  unsigned short out;

  if(Flow_last_end > Flow_cursor){//  move data to start of buffer.
    for(int i = 0; i < Flow_cursor; i++){ // copy start of dat over to make room for tail
      Flow_msg[FLOW_MSG_LEN - Flow_last_end + i] = Flow_msg[i];
    }
    for(int i = 0; i < FLOW_MSG_LEN - Flow_last_end; i++){ // copy tail over to start
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
  return;
}

