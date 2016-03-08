#include "Arduino.h"
#include <SoftwareSerial.h>


const unsigned long BAUDRATE = 115200;

// ERROR CODES **********************************
const byte ROLLOVER_ERROR = 2;

//************************************************

// Tolerances
const unsigned short CUFF_TOLL = 300; // mmhg

/*
** Message format:
*
 * BYTE# Type           Purpose
 * 0     byte           Message ID = 1
 * 1-4   unsigned long  Milliseconds since last reset (unsigned int)
 * 5-6   unsigned short Cuff Pressure (Units??)  
 * 7-8  unsigned short Flow Rate (Units ??)
 * 9-10 unsigned short Pulse Reading (Units??)
 * 11   byte           Check Sum
 */
const byte        MEASUREMENTS_PID = 1;
const byte              STATUS_PID = 2;
const byte               SHORT_PID = 'R';
const byte LORATE_MEASUREMENTS_PID = 3;
const byte        MEASUREMENTS_LEN = 11; // all bytes excluding cksum
const byte LORATE_MEASUREMENTS_LEN = 9; // all bytes excluding cksum

// STS21 constants
const byte  STS_ADDR           = 0b1001010;
const byte  STS_HOLD_MASTER    = 0b11100011;
const byte  STS_NOHOLD_MASTER  = 0b11110011;
const byte  STS_WRITE_USER_REG = 0b11100110;
const byte  STS_READ_USER_REG  = 0b11100111;
const byte  STS_SOFT_RESET     = 0b11111110;
const float STS_T0             = -46.85;
const float STS_GAIN           = 175.72;

// pin assignments
const byte     PUMP_PIN = 9;
const byte    VALVE_PIN = 4;
const byte    PULSE_PIN = 1;
const byte          LED = 13;
const byte      FLOW_TX = 2;
const byte      FLOW_RX = 4;

// other constants
const byte      COMMAND_BUFF_SIZE = 32;   // command buffer size
const byte         COMMAND_LENGTH = 9;    // command buffer size
const byte          COMMAND_START = 0x7F; // first two bytes of command
const byte            COMMAND_END = '\n'; // last bytes of command
const byte  HIRATE_DATA_BUFF_SIZE = 15;   // data buffer size
const byte  LORATE_DATA_BUFF_SIZE = 1;   // data buffer size
const byte     READY_FOR_NEW_DATA = 1;
const byte    CUFF_PRESSURE_ERROR = 1;
const byte    MAX_TEST_TIME_ERROR = 2; // mS
const unsigned long MAX_TEST_TIME = 1000 * 60 * 12; // 1000 * 60 * 12; // 12 minutes
const int   VALVE_OPEN = 1;
const int VALVE_CLOSED = 0;
const byte FLOW_BUFFER_LEN = 8; // enough bytes for two valid samples
const byte FLOW_MAX_TRY = 20; // max # tries to read flow meter
const unsigned short FLOW_MAX_COUNT = 30000;
const byte SAMPLE_INTERVAL_STEP_MS = 4;

// I2C Addresses
const byte    DS3231_ADDR = 104;
const byte AMB_PRESS_ADDR = 120; // 0b1111000;


// pointers
byte command[COMMAND_BUFF_SIZE];   // commands
byte hirate_data[HIRATE_DATA_BUFF_SIZE];         // high rate data
byte lorate_data[LORATE_DATA_BUFF_SIZE];         // low rate data
byte *pump_state_p = command + 3;
byte *valve_state_p = command + 4;
byte *cuff_pressure_p = hirate_data + 5;
byte *flow_rate_p = command + 7;


// global vars
boolean sampling = false;             // are we currently sampling?
char flow_buffer[FLOW_BUFFER_LEN];              
byte flow_buffer_idx = 0;             // last buffer index
unsigned long next_sample_ms = 0L;    // when to take the next sample in miliseconds millis(), 
unsigned long interval_ms = 0L;       // interval between samples in ms
unsigned long lr_next_sample_ms = 0L; // when to take the next low rate sample in miliseconds millis(), 
unsigned long lr_interval_ms = 1000L;    // interval between low rate samples in ms
long pressure_start;                  // -1 for valve open
volatile int pulse_signal;            // holds the incoming raw pulse data
volatile int flow_rate;               // holds the incoming raw pulse data
boolean valve_is_closed = true;

byte short_msg[3] = {SHORT_PID};      // buffer for short messages, must start with 'R'.
byte status_msg[5] = {STATUS_PID};    // buffer for status messages, must start with STATUS_PID.

byte Flow_cursor = 0;
byte Flow_last_end = 0;
bool Flow_new_data = false;
const byte FLOW_MSG_LEN = 100;
char Flow_msg[FLOW_MSG_LEN + 1];
char Flow_rate[2];

unsigned long loop_count = 0;

SoftwareSerial Flow_serial(FLOW_TX, FLOW_RX, true); // Serial interface to flow sensor

template<class T> inline Print &operator <<(Print &obj, T arg){obj.print(arg); return obj;} 


/*
 * compute check sum, send data
 * 
 * dat -- pointer to message data
 *   n -- number of message bytes (not including check sum)
 */
void send_msg(byte *dat, byte n);

/*
 * Initialize pump
 */
void pump_setup();

/*
 * Initialize flow meter
 */
void flow_setup();

/*
 * Initialize pressure sensor
 */
void pressure_setup();

/*
 * Initialize valve
 */
void valve_setup();

/*
 * Pump at given rate for duration in miliseconds.
 * rate = 0: off
 */
void control_pump(int rate);
void pump_off();

/*
 * Open valve
 * full closed 0 <= dc <= 1(full open)
 */
void control_valve(byte duty_cycle);
void valve_close();
void valve_open();

/*
 * Start sampling pressure sensor at given rate (20 Hz max)
 */
void start_sampling(unsigned long interval_ms);
void stop_sampling();

void sample();


/*
 * read serial stream into command buffer.  First byte is offset
 * return true when valid command is received
 */
boolean serial_interact();

void bpc_setup();

void setup();

void loop();

// convience functions
