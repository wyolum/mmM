'''
uControl driver library.
'''

from numpy import *
import time
import sys
import struct
from serial import *
from glob import *
import pylab 
import os.path
from constants import *

#         name   lo    hi   unit
LIMITS = {'GAGE':(0,  400, 'MMHG'),
          'FLOW':(-1000, 1000, 'SCCM'),
          'ABS_PRESSURE':(5, 1500, 'MBAR'),
          'TEMP':(0, 30, 'C')
          }

def limit_check(val, name):
    lo, hi, unit = LIMITS[name]
    if lo > val:
        val = lo
    if val > hi:
        val = hi
    return val

def mmhg_to_count(val):
    # count = val * 15030 / 280. + 2470 ### was
    # return count                      ### orig
    b, m = [ 2599.61459873,    58.94583836] ## calibrated one unit
    return m * val + b

def count_to_mmhg(val):
    # return (val - 2470) * 280 / 15030. ## orig
    b, m = [ 2599.61459873,    58.94583836] ## calibrated one unit
    return (val - b) / m

## 200 mlps
SENSIRION_SCALE_FACTOR_F = 140
SENSIRION_OFFSET_F  = 32000
# /* (count - SENSIRION_OFFSET_F) / float(SENSIRION_SCALE_FACTOR_F); */

## 20 mlps
# SENSIRION_SCALE_FACTOR_F = 1
# SENSIRION_OFFSET_F  = 0
def count_to_smlpm(count):
    smlpm = float(count - SENSIRION_OFFSET_F) / float(SENSIRION_SCALE_FACTOR_F) * 1000;
    return smlpm

def mmhg_to_mb(val):
    return  val * 1.33322368

def mb_to_mmhg(val):
    return val /  1.33322368

COMMAND_START = chr(0x7f) + chr(0x7f)
COMMAND_END = '\n'
last_cmd = None
done = False
baudrate = 115200
timeout = .01

    
def getValveByte(valve0=False, valve1=False):
    return 1<<7 | bool(valve0) | bool(valve1) << 1

# s.rtscts = True
#         [init,  interval, pump_rate, valve, status]

### Message defaults!
__cmd__ = [False,           0,         0,     0,      0]
def send_cmd(init=None, interval=None, pump_rate=None, valve=None,
             cuff_pressure=False,
             flow_rate=False,
             pulse=False,
             amb_pressure=False,
             amb_temp=False,
             pump_state=False,
             valve_state=False,
             ):
    ## grab defaults
    if init is None:
        init = __cmd__[0]
    if interval is None:
        interval = __cmd__[1]
    if pump_rate is None:
        pump_rate = __cmd__[2]
    if valve is None:
        valve = __cmd__[3]
    # else:
    #     valve = 1 << 7 | bool(valve0) | bool(valve1) << 1

    __send_cmd(init=init,
               interval=interval,
               pump_rate=pump_rate,
               valve=valve,
               cuff_pressure=cuff_pressure,
               flow_rate=flow_rate,
               pulse=pulse,
               amb_pressure=amb_pressure,
               amb_temp=amb_temp,
               pump_state=pump_state,
               valve_state=valve_state)
               
CUFF_PRESSURE_BIT = 0
FLOW_RATE_BIT = 1
PULSE_RATE_BIT = 2
AMB_PRESSURE_BIT = 3
AMB_TEMP_BIT = 4
PUMP_STATE_BIT = 5
VALVE_STATE_BIT = 6

GAGE_MIN_COUNT = 2500
GAGE_MAX_COUNT = 24575 # 0x5fff
GAGE_COUNT_RANGE = GAGE_MAX_COUNT
GAGE_MAX_PRESSURE_MB = 2000
GAGE_SENSITIVITY = float(GAGE_COUNT_RANGE) / GAGE_MAX_PRESSURE_MB

__command_buffer = []
def __send_cmd(init, 
               interval, 
               pump_rate, 
               valve, 
               cuff_pressure,
               flow_rate,
               pulse,
               amb_pressure,
               amb_temp,
               pump_state,
               valve_state,
               ):
    global last_cmd
    init = [0, 1][init]

    ## fill out status request byte (Can cause sample delay)
    status_req = ((cuff_pressure << CUFF_PRESSURE_BIT) | 
                  (    flow_rate << FLOW_RATE_BIT)     | 
                  (        pulse << PULSE_RATE_BIT)    | 
                  ( amb_pressure << AMB_PRESSURE_BIT)  | 
                  (     amb_temp << AMB_TEMP_BIT)      | 
                  (   pump_state << PUMP_STATE_BIT)    | 
                  (  valve_state << VALVE_STATE_BIT))
    cmd = [init, interval, pump_rate, valve, status_req]
    for i in range(5): ## copy state to defaults for next call to send_cmd
        __cmd__[i] = cmd[i]
    # cksum = chr(211)
    # print 'cmd"%s"' % cmd
    cksum = (sum([c for c in cmd]) + 0xA) % 256
    cmd = COMMAND_START + chr(cksum) + ''.join([chr(v) for v in cmd]) + COMMAND_END
    s.write(cmd)
    # __command_buffer.append(cmd)
    # s.flush()
    # time.sleep(.5)
    last_cmd = cmd

def connect():
    global s
    patt = '/dev/ttyUSB*'
    for port in glob(patt):
        s = Serial(port, baudrate, timeout=timeout)
        break
connect()
    
class PIDError(Exception):
    pass
class LengthError(Exception):
    pass
class CheckSumError(Exception):
    pass
class PID(object):
    '''
    Abstract class
    '''
    PID = None
    PAYLOAD_FMT = None
    
    def __init__(self, packet):
        if packet[0] != self.PID:
            raise PIDError('PIDError: %s != %s' % (packet[0], self.PID))
        if len(packet) < self.N_BYTE:
            raise LengthError('LengthError: %s < %s' % (len(packet), self.N_BYTE))
        packet = packet[:self.N_BYTE]

        s = sum([ord(c) for c in packet[:-1]]) % 256
        if chr(s) != packet[-1]: 
            print map(ord, packet)
            raise CheckSumError('CheckSumError: %s != %s' % (s, ord(packet[-1])))

        ### Valid packet beyond here
        payload = packet[1:-1]
        if self.PAYLOAD_FMT:
            # print 'Good packet', map(ord, packet)
            payload = struct.unpack(self.PAYLOAD_FMT, payload)
        self.payload = payload
    def __getitem__(self, i):
        return self.payload[i]
    def __repr__(self):
        return '%s-%s' % (self.__class__.__name__, self.payload)

PID_file = open("Flow3.txt", 'wb')
class MeasurementsPID(PID):
    '''
    High rate data format:
    bytes   type                 desc
    0123     unsigned integer -- time in ms since reset   [0]
    45       unsigned short   -- cuff pressure            [1]
    67       unsigned short   -- flow                     [2]
    89       unsigned short   -- pulse                    [3]
    '''
    PID = chr(1)
    # PAYLOAD_FMT = 'IHhH' ## pack tightly ## orig pulse sensor
    PAYLOAD_FMT = 'IHhh' ## pack tightly   ## using pulse slot for second flow meter
    N_BYTE = struct.calcsize(PAYLOAD_FMT) + 2

    def __init__(self, packet):
        PID.__init__(self, packet)
        self.millis = self[0]
        self.cuff = limit_check(count_to_mmhg(self[1]), 'GAGE') ## in mmhg
        self.flow = limit_check(count_to_smlpm(self[2]), 'FLOW')
        self.pulse = self[3]
        print >> PID_file, self.flow, self.pulse
        
class ShortPID(PID):
    '''
    Short 2-char message from device.
    '''
    PID = 'R'
    PAYLOAD_FMT = 'cc'
    N_BYTE = struct.calcsize(PAYLOAD_FMT) + 2

class StatusPID(PID):
    '''
    status packet format
    
    byte
    0 -- device value
    1 -- device ID
    
    '''
    PID = chr(2)
    PAYLOAD_FMT = 'HB'
    N_BYTE = struct.calcsize(PAYLOAD_FMT) + 2
    NAMES = ['Cuff Pressure',
             'Flow Rate',
             'Pulse Measure',
             'Amb Pressure',
             'Amb Temp',
             'Pump',
             'Valve',
             'Interval']
    convert = {3: lambda bits: (bits - AMB_PRESSURE_MIN_COUNT) / AMB_PRESSURE_SENSITIVITY,
               4: lambda bits: STS_T0 + (STS_GAIN * bits) / float(1l << 16)}
                   
    def __init__(self, packet):
        PID.__init__(self, packet)
        self.devid = self[1]
        self.name = self.NAMES[self.devid]
        if self.devid in self.convert:
            self.value = self.convert[self.devid](self[0])
        else:
            self.value = self[0]
        print self
    def __repr__(self):
        return 'Status:%s=%s' % (self.name, self.value)
        
MPID = MeasurementsPID

## all valid packet types
PIDS = {MPID.PID: MPID,
        ShortPID.PID:ShortPID,
        StatusPID.PID:StatusPID}
assert chr(1) in PIDS

messages = []
last_ser_data = ''
def read_packet():
    global last_ser_data
    
    ## read in remainder of packet
    new_data = s.read(MeasurementsPID.N_BYTE - len(last_ser_data))
    if new_data:
        pass
        # print new_data
    # if new_data:
    #     print 'new_data', new_data
    ser_data = last_ser_data + new_data
    if ser_data == '':
        packet = None
    elif ser_data[0] in PIDS: ## packet ID in first byte
        try:
            packet = PIDS[ser_data[0]](ser_data)
            last_ser_data = ser_data[packet.N_BYTE:]
        except LengthError, e:
            print e ## DBG LOG
            packet = None ## not long enough, get more data on next call
        except CheckSumError, e:
            print e ## DBG LOG
            last_ser_data = ser_data[1:]
            packet = None ## malformed, try again at one byte offset next call
    else:
        last_ser_data = ser_data[1:] ## not the start of an MPID

        # DBG LOG
        # print 'Not a valid mpid', ser_data[0], PIDS.keys(), map(ord, ser_data[0]), map(ord, PIDS.keys())
        packet = None
    return packet

subscriptions = {}

def subscribe(pid, callback):
    '''
    subscribe to recieve packets with id == pid
    '''
    if pid not in subscriptions:
        subscriptions[pid] = []
    subscriptions[pid].append(callback)

def unsubscribe(pid, callback):
    if subscriptions.has_key(pid):
        if callback in subscriptions[pid]:
            subscriptions[pid].remove(callback)
__n_repeat = 0
def repeat_last_cmd():
    global __n_repeat
    if last_cmd:
        __n_repeat += 1
        print 'repeating last command, %s repeats so far' % __n_repeat
        s.write(last_cmd)
def garbeled_cmd_catcher(pkt):
    if pkt[0] == 'C':
        if pkt[1] in 'SCL':
            repeat_last_cmd()
def serial_ready_catcher(pkt):
    if pkt[0] == 'S':     # serial
        if pkt[1] == 'R': # ready
            while __command_buffer:
                cmd = __command_buffer.pop(0)
                print 'writing', cmd
                s.write(cmd)
                
    
subscribe(ShortPID.PID, garbeled_cmd_catcher)
subscribe(ShortPID.PID, serial_ready_catcher)
def serial_interact_once():
    out = False
    p = read_packet()
    if p:
        if p.PID in subscriptions:
            for callback in subscriptions[p.PID]:
                callback(p)
                out = True
    return out

def serial_interact(max_iter=10, abort=None):
    if abort is None:
        abort = lambda: False
    iter = 0
    while serial_interact_once() and iter < max_iter and not abort():
        iter += 1

def serial_loop(stop_condition):
    while not stop_condition():
        serial_interact()

heart = []
def status__test__():
    s.flush()
    send_cmd(interval=0)   # stop sampling
    dat = s.read(100)
    reset()

    send_cmd(valve=1, pump_rate=1)
    send_cmd(cuff_pressure=True,
             flow_rate=True,
             pulse=True,
             amb_pressure=True,
             amb_temp=True,
             pump_state=True,
             valve_state=True
             )
    for i in range(5):
        read_packet()
    for i in range(2):
        pkt = read_packet()
        assert pkt[0] == 1
    send_cmd(valve=0, pump_rate=0)
    send_cmd(cuff_pressure=True,
             flow_rate=True,
             pulse=True,
             amb_pressure=True,
             amb_temp=True,
             pump_state=True,
             valve_state=True
             )
    for i in range(5):
        read_packet()
    for i in range(2):
        pkt = read_packet()
        assert pkt[0] == 0
def toggle_rts():
    print 'Resetting from FTDI...'
    s.flushInput()
    s.setRTS(True); time.sleep(.1); s.setRTS(False) ## reset uControl

def toggle_GPIO18():
    print 'Resetting from GPIO...'
    GPIO.output(18, GPIO.LOW)
    time.sleep(.1); 
    GPIO.output(18, GPIO.HIGH)

def reset():
    '''
    initialize the serial connection with the device by requesting pump state.
    '''
    global last_ser_data
    print 'Resetting uControl'
    toggle = toggle_rts
    toggle()
    time.sleep(2.1)
    ack = None
    interval = 5
    while ack is None:
        # 20 tries
        for i in range(20):
            print 'try', i
            ack = read_packet()
            if isinstance(ack, ShortPID):
                if ack[0] == 'R' and ack[1] == '!':
                    break
            time.sleep(.1)
        else:
            # resend request
            s.flushInput()
            print 'try again'
            toggle()
            time.sleep(3.1)
            send_cmd(pump_state=True)
    print 'uControl is reset'
def ping__test__():
    s.flush()
    ## reset()
    send_cmd(pump_state=1)
    for i in range(10):
        send_cmd(pump_state=1)
        start = time.time()
        while not read_packet():
            pass
        print time.time() - start
# ping__test__() ## .01 seconds on toshiba laptop
# ping__test__() ## .0003 seconds on raspberry pi 3
# here

def stream__test__():
    # s.flush()
    # s.setRtsCts(False); s.setRtsCts(True)
    # time.sleep(1)
    print 'start'
    try:
        # reset()
        sample_num = 0
        start = time.time()
        def go(packet):
            global done
            initial_millis = None
            N = 0
            while N < 10000:
                pkt = read_packet()
                if N % 1000 == 0:
                    pass
                    # send_cmd()
                if pkt:
                    if isinstance(pkt, MPID):
                        N += 1
                        if initial_millis is None:
                            initial_millis = pkt.millis
                            last_millis = pkt.millis
                        heart.append(pkt.pulse)
                        dt = float(time.time() - start) 
                        rate = (pkt.millis - initial_millis) / dt
                        print 'Valid PKT:', pkt, (pkt.millis - last_millis), (pkt.millis - initial_millis) / float(N), 'ms/sample'
                        last_millis = pkt.millis
            ha = array(heart)
            uptime = pkt.millis / 3.6e6
            print 'UP TIME:', int(uptime), 'Hr', int(uptime * 60) % 60, 'Min', int(uptime * 3600) % 60, 'Sec'
            # send_cmd(interval=0)
            done = True

        subscribe(StatusPID.PID, go)
        RATE = 1
        # send_cmd(interval=RATE, pump_state=True)
        while not done:
            print done, len(last_ser_data)
            for i in range(10):
                serial_interact()
            if not done:
                send_cmd(interval=RATE, pump_state=True)


    finally:
        print 'finally'
        unsubscribe(StatusPID.PID, go)
        # send_cmd(interval=0)
        # s.flush()
    
def abort__test__():
    reset()
    try:
        send_cmd(pump_rate=True, valve=1, interval=0)
        packet = read_packet()
        assert packet[0] == 'S'
        assert ord(packet[1]) == 0
        
        send_cmd(valve_state=True, )
        packet = read_packet()
        assert packet[0] == 'S'
        assert ord(packet[1]) == 0
        packet = read_packet()
        assert packet[0] == 1
        send_cmd(valve=True, valve_state=True)
        print 'b4', read_packet()
        print 'b4', read_packet()
        print 'after', read_packet()
        for i in range(5):
            print i, read_packet()
            time.sleep(1)
    finally:
        send_cmd(valve=0, pump_rate=0, interval=0) ## turn off sampling
        s.flushInput()
        pass
        
if __name__ == '__main__':
    print 'stream__test__'
    stream__test__()
