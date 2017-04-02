'''
based on przemoli-pygametutorial-540433c50ffc
'''

import sys; sys.path.append('../../python')
import re
import os
import time
import math
import datetime
from numpy import array
import pickle
import glob
import pylab

import util
import drive
import uControl

MAX_PRESSURE = 300 ### shutoff above this pressure
MIN_PRESSURE = 35

MMM_DATA = dict(init=False,
                interval=1,
                pump_rate=0,
                valve=0, ## for valve0 and valve1 control
                pump_state=True,
                amb_pressure=True,
                amb_temp=True,
                valve_state=True, ## for valve status request
               )
def mmm_update():
    '''
    Send commands to mmm board
    '''
    for k in MMM_DATA:
        MMM_DATA[k] = int(MMM_DATA[k])
    drive.send_cmd(**MMM_DATA)

def mmm_new_status(packet):
    '''
    Update leds when new status arrives.
    '''
    pass
DEG = math.pi / 180.
WIDTH = 800
HEIGHT = 480
WIDTH = 480
HEIGHT = 272

last_cuff_pressure = 123
hirate = []
recording = False
MAX_HIRATE_N = 200 * 60 * 2
def start_recording():
    global recording
    del hirate[:]
    recording = True

def stop_recording():
    global recording
    recording = False

def mpid_cb(pkt):
    global last_cuff_pressure
    last_cuff_pressure = last_cuff_pressure * .50 + pkt.cuff * .50
    # print last_cuff_pressure
    if recording:
        hirate.append([pkt.millis, pkt.cuff, pkt.flow, pkt.pulse])
        if len(hirate) > MAX_HIRATE_N:
            del MAX_HIRATE[-MAX_HIRATE_N:]


drive.subscribe(drive.MPID.PID, mpid_cb)
drive.subscribe(drive.StatusPID.PID, mmm_new_status)

def bpc_run(pkl_fn):
    print 'here we go'
    # while s.read(100000):
    #     print 'flush serial'
    uc = uControl.uControl()
    # junk = s.read(1000)
    print 'here'
    try:
        if not os.path.exists(pkl_fn):
            print 'uc.cuff_pressure', uc.cuff_pressure
            print 'maintain()'
            uc.maintain(250, 280, 3)
            uc.record(True)
            print 'len(uc.hirate)', len(uc.hirate)
            while uc.pump_state:
                print 'uc.cuff_pressure', uc.cuff_pressure
                serial_interact()
            print 'deflate'
            uc.deflate(5, fast=False)
            ## uc.deflate(5, fast=True)
            uc.record(False)
            if len(uc.hirate) > 0:
                pickle.dump(uc.hirate, open(pkl_fn, 'wb'))
                print 'write', pkl_fn
        hirate = pickle.load(open(pkl_fn, 'rb'))
        print hirate[0]
        print 'len(uc.hirate)', len(hirate)
        hirate = array(hirate)
            
        dt = 0.004
        n_tap = 100
        lp_taps = util.get_lowpass_taps(.6, dt, n_tap)
        llp_taps = util.get_lowpass_taps(.4, dt, n_tap)
        lpd = util.filter(hirate[:,1] - hirate[0, 1], lp_taps)[::10] + hirate[0, 1]
        llpd = util.filter(hirate[:,1] - hirate[0, 1], llp_taps)[::10] + hirate[0, 1]
        print len(lpd)
        times = hirate[::10,0]
        ax = pylab.subplot(211)
        pylab.plot(times, lpd)
        pylab.plot(times, llpd)
        pylab.subplot(212, sharex=ax)
        pylab.plot(times, lpd - llpd)
        pylab.figure()
        pylab.plot(hirate[:,2])
        pylab.show()
        
        # pylab.figure(2); pylab.plot(uc.lpf.out)
        # pylab.figure(3); pylab.plot(hirate[:,1])
        
        print 'done'
    finally:
        uc.deflate(50)
        uControl.send_cmd(pump_rate=False, valve=drive.getValveByte(valve0=True))
        time.sleep(2)
        uControl.send_cmd(pump_rate=False, valve=drive.getValveByte(valve0=False), interval=0)
    pylab.show()

USAGE = '''\npython InVitro.py out_filename.pkl\n'''

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print USAGE
    else:
        bpc_run(sys.argv[1])
