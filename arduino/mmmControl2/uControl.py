import sys
sys.path.append("../../python/")
import pickle
import scipy.signal as signal
import numpy
import util
import pylab
import time
from drive import *
from constants import *

class uControl:
    '''
    Behind the scenes interface to uControl.
    '''
    def __init__(self, listener=None, dummy=False):
        self.__abort = False
        self.recording = False      # flag to indicate times when data is to be captured
        self.hirate = []            # store hirate data when recording
        self.lorate = []            # not used
        self.mpid_count = 0
        self.lpid_count = 0         # not used

        ## uControl readings
        self.cuff_pressure = None   
        self.flow_rate = None
        self.pulse_rate = None
        self.amb_pressure = None
        self.amb_temp = None
        self.pump_state = None
        self.valve_state = getValveByte(False, False)
        self.short_msg = None
        self.last_update = None
        self.bleeding = False
        
        ## used to control inflation and deflation
        self.max_pressure = 1e6
        self.min_pressure = -1
        self.listener = listener
        
        self.dt = 0.004  ## DO NOT Change without also changing uControl firmware
        self.n_tap = 20
        self.lp_taps = util.get_lowpass_taps(10, self.dt, self.n_tap) ## 0 - 5 Hz filter for data
        self.lpf = util.StreamingFir(self.lp_taps, 2500, 10)
        
        ## get notifed of new messages from uControl firmware
        subscribe(MPID.PID, self.mpid_cb)
        subscribe(ShortPID.PID, self.short_cb)
        subscribe(StatusPID.PID, self.status_cb)

        ### connect to uControl hardware
        send_cmd(cuff_pressure=True, interval=1)   ## interval=1 ==> .004 sec dt
        tries = 0
        if not dummy:
            while self.cuff_pressure is None:
                serial_interact()
                tries += 1
                if tries % 10 == 9:
                    print 'tries', tries
        # self.send_cmd(valve=self.valve_state)
                    
    def send_cmd(self, **kw):
        '''
        double check actuators respond
        '''
        out = send_cmd(**kw)
        if 'valve' in kw or 'pump' in kw:
            self.delay(.5)
            if ((self.valve_state & 0b01111111) != (kw['valve'] & 0b01111111) 
                or self.pump_state != kw['pump']):
                out = send_cmd(**kw)
                self.delay(.5)
                if ((self.valve_state & 0b01111111) != 
                    (kw['valve'] & 0b01111111)
                    or self.pump_state != kw['pump']):
                    raise Exception('uControl not responding')
                
    def mpid_cb(self, pkt):
        '''
        Called when a new measurement packet is recieved (hirate)
        '''
        if self.listener:
            self.listener.mpid_cb(pkt)
        self.lpf(pkt.cuff)
        self.mpid_count += 1
        # print pkt
        if self.recording:
            self.hirate.append([pkt.millis, pkt.cuff, pkt.flow, pkt.pulse])
        self.cuff_pressure = pkt.cuff
        self.flow_rate = pkt.flow
        self.pulse_rate = pkt.pulse
        if self.lpf.last > self.max_pressure and self.pump_state:
            print 'max pressure exceeded, pump off', self.cuff_pressure, self.min_pressure, self.max_pressure
            self.pump_state = False
            send_cmd(pump_rate=self.pump_state)
        if self.lpf.last < self.min_pressure and not self.pump_state:
            print 'min pressure exceeded, pump on', self.cuff_pressure, self.min_pressure, self.max_pressure
            self.pump_state = True
            send_cmd(valve=getValveByte(valve0=False, valve1=False))
            send_cmd(pump_rate=self.pump_state)
        if False:
            any_open    = bool(0b00000011 & self.valve_state)
            both_closed = not any_open
            if self.lpf.last <= (self.max_pressure + self.min_pressure) / 2. and self.bleeding:
                print 'stop the bleeding'
                self.valve_state = getValveByte(valve0=False, valve1=False)
                send_cmd(valve=self.valve_state)
                self.bleeding = False

            if self.lpf.last > self.max_pressure and both_closed and not self.bleeding:
                print 'start the bleeding'
                ### if valves are both closed, start bleeding
                self.valve_state = getValveByte(valve0=True, valve1=False)
                send_cmd(valve=self.valve_state)
                self.bleeding = True
            
            
    def lpid_cb(self, pkt):
        '''
        Called when a new lorate measurement packet is recieved (lorate)
        '''
        if self.listener:
            self.listener.lpid_cb(self, pkt)
        self.lpid_count += 1
        # print pkt
        if self.recording:
            self.lorate.append([pkt.millis, pkt.amb_pressure, pkt.amb_temp])
        self.amb_pressure = pkt.amb_pressure
        self.amb_temp = pkt.amb_temp

    def short_cb(self, pkt):
        '''
        Called when a new short packet is recieved (two chars)
        '''
        if self.listener:
            self.listener.short_cb(pkt)
        self.short_dat = pkt[0] + pkt[1]
        
        print "short msg: 0X%02x%02x" % (ord(pkt[0]), ord(pkt[1]))
        
    def status_cb(self, pkt):
        '''
        Called when a new status packet is recieved
        '''
        if self.listener:
            self.listener.status_cb(self, pkt)
        if pkt.name == 'Cuff Pressure':
            self.cuff_pressure = pkt.value
        elif pkt.name == 'Flow Rate':
            self.flow_rate = pkt.value
        elif pkt.name == 'Pulse Measure':
            self.pulse_rate = pkt.value
        elif pkt.name == 'Amb Pressure':
            self.amb_pressure = pkt.value
        elif pkt.name == 'Amb Temp':
            self.amb_temp = pkt.value;
        elif pkt.name == 'Pump':
            self.pump_state = pkt.value
        elif pkt.name == 'Valve':
            self.valve_state = pkt.value

    def inflate(self, mmhg, abort):
        '''
        inflate cuff to mmhg pressure.
        abort -- callback function
                 return False if inflation should continue
                 return True if inflation should be aborted
        '''
        self.min_pressure = mmhg
        self.max_pressure = self.min_pressure + 10 # mmhg
        if self.cuff_pressure < self.min_pressure and not abort():
            while self.cuff_pressure < self.min_pressure and not abort():
                serial_interact(10, abort)
        # send_cmd(pump_rate=False) # turn off pump
    
    def maintain(self, min_p, max_p, duration=10, abort=None):
        '''
        maintain pressure between min_p and max_p for duration seconds
        abort -- callback function
                 return True if pressure should maintained
                 return False if pressure should be released
        '''
        if abort is None:
            abort = lambda :False
        
        self.inflate(max_p, abort)
        self.min_pressure = min_p
        self.max_pressure = max_p
        start = time.time()
        i = 0
        print 'hold'
        last_togo = -1
        while time.time() < start + duration and not abort():
            serial_interact(max_iter=10, abort=abort)
            togo = int(start + duration  - time.time())
            if int(togo) != last_togo:
                print togo, 'sec togo'
                last_togo = togo
        if abort():
            self.pump_state = False
            send_cmd(pump_rate=self.pump_state)
            self.deflate(10)

    def deflate(self, mmhg, fast=False):
        '''
        Open valve until mmhg is reached
        '''
        self.min_pressure = -1              ## make sure pump does not come on
        self.max_pressure = mmhg
        if self.cuff_pressure > self.max_pressure:
            send_cmd(valve=getValveByte(valve0=True, valve1=fast))
        
        while self.cuff_pressure > self.max_pressure:
            serial_interact()
        send_cmd(valve=getValveByte(valve0=False, valve1=False), 
                 valve_state=True)
        
    def record(self, recording=True):
        '''
        Start or stop storing hirate data
        '''
        self.recording = recording

    def delay(self, seconds):
        '''
        Delay while monitoring serial
        '''
        start = time.time()
        while time.time() < start + seconds:
            serial_interact()
            
    def abort(self):
        self.__abort = True
        self.deflate(10)
        self.max_pressure = 0
        self.min_pressure = -1

def test():
    print 'here we go'
    # while s.read(100000):
    #     print 'flush serial'
    uc = uControl()
    # junk = s.read(1000)
    print 'here'
    try:
        print 'uc.cuff_pressure', uc.cuff_pressure
        print 'maintain()'
        uc.maintain(200, 230, 3)
        uc.record(True)
        print 'len(uc.hirate)', len(uc.hirate)
        while uc.pump_state:
            print 'uc.cuff_pressure', uc.cuff_pressure
            serial_interact()
        print 'deflate'
        uc.deflate(2, fast=False)
        # uc.deflate(5, fast=True)
        uc.record(False)
        print 'len(uc.hirate)', len(uc.hirate)
        hirate = array(uc.hirate)
        if len(uc.hirate) > 0:
            dt = 0.004
            n_tap = 100
            lp_taps = util.get_lowpass_taps(5, dt, n_tap)
            llp_taps = util.get_lowpass_taps(.25, dt, n_tap)
            lpd = util.filter(hirate[:,1] - hirate[0, 1], lp_taps)[::10] + hirate[0, 1]
            llpd = util.filter(hirate[:,1] - hirate[0, 1], llp_taps)[::10] + hirate[0, 1]
            print len(lpd)
            times = hirate[::10,0]
            ax = pylab.subplot(211)
            pylab.title('low pass')
            pylab.plot(times, lpd)
            pylab.plot(times, llpd)
            pylab.subplot(212, sharex=ax)
            # pylab.plot(times, lpd - llpd)
            # pylab.figure()
            pylab.plot(hirate[:,0], hirate[:,2])
            pylab.title('flow')
            pylab.show()
            
            pfn = 'hirate.pkl'
            pickle.dump(hirate, open(pfn, 'w'))
            print 'wrote', pfn
            # pylab.figure(2); pylab.plot(uc.lpf.out)
            # pylab.figure(3); pylab.plot(hirate[:,1])

        print 'done'
    finally:
        uc.deflate(50)
        send_cmd(pump_rate=False, valve=getValveByte(valve0=True))
        time.sleep(2)
        send_cmd(pump_rate=False, valve=getValveByte(valve0=False), interval=0)
    pylab.show()

if __name__ == '__main__':
    test()

