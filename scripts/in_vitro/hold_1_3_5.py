import argparse
import sys; sys.path.append('../../python')
#import cuff_compliance
import re
import os
import time
import math
import datetime
from numpy import array, log, exp, linalg, ones, zeros, dot, diff, arange, argmax
import pickle
import glob
import pylab

import util
import drive
import uControl

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

def gage_fit(time, gage):
    log_gage = log(gage)
    g_coeff = util.poly_fit(time, log_gage, 1) ## new way test
    gage_fit = exp(util.poly_eval(g_coeff, time))
    err = linalg.norm(gage - gage_fit)
    return gage_fit, g_coeff

HONEYWELL_OFFSET = -75.840574
HONEYWELL_SLOPE = 0.025600
def endys_run(pkl_fn, hold_sec):
    try:
        if not os.path.exists(pkl_fn):
            uc = uControl.uControl()
    
            print 'uc.cuff_pressure', uc.cuff_pressure
            print 'maintain()'
            uc.inflate(250, lambda *args: False)
            uc.maintain(250, 260, hold_sec)
            uc.record(True)
            print 'len(uc.hirate)', len(uc.hirate)
            while uc.pump_state:
                print 'uc.cuff_pressure', uc.cuff_pressure
                drive.serial_interact()
            print 'deflate'
            uc.deflate(20, fast=False)
            ## uc.deflate(5, fast=True)
            uc.record(False)
            if len(uc.hirate) > 0:
                pickle.dump(uc.hirate, open(pkl_fn, 'wb'))
                print 'write', pkl_fn
    finally:
        try:
            uc.deflate(50)
            uControl.send_cmd(pump_rate=False, valve=drive.getValveByte(valve0=True))
            time.sleep(2)
            uControl.send_cmd(pump_rate=False, valve=drive.getValveByte(valve0=False), interval=0)
        except:
            pass

def my_plot(pkl_fn, peak_marker, trough_marker):
    hirate = pickle.load(open(pkl_fn, 'rb'))
    print hirate[0]
    print 'len(uc.hirate)', len(hirate)
    hirate = array(hirate)
    # hirate = hirate[hirate[:,1] < 200] ## filter out really high pressure

    dt = 1/200.
    n_tap = 1000
    dec = 1
    lp_taps = util.get_lowpass_taps(1, dt, n_tap)
    llp_taps = util.get_lowpass_taps(.05, dt, n_tap)
    gage = hirate[:,1]
    lpd = util.filter(gage - gage[0], lp_taps)[::dec] + gage[0]
    llpd = util.filter(gage - gage[0], llp_taps)[::dec] + gage[0]
    bandpass = lpd - llpd

    skip_factor = 1.
    skip = int(n_tap * skip_factor)

    gage = gage[skip:]
    lpd = lpd[skip:]
    llpd = llpd[skip:]
    bandpass = bandpass[skip:]
    hirate = hirate[skip:]

    ## deltas are peaks(on the left) - troughs(on the right)
    try:
        troughs, peaks, deltas = util.get_troughs_peaks_deltas(bandpass)
    except ValueError:
        troughs = arange(0, len(bandpass), 200)
        peaks = troughs + 100
        deltas = peaks - troughs
    print len(peaks), len(troughs), len(deltas)
    ## adj deltas are trought(on the left) - peaks (on the right)
    adj_deltas = deltas + (llpd[troughs] - llpd[peaks])
    flow = hirate[::dec,2]
    flow_lp = util.filter(flow - max(flow), lp_taps)[::dec] + max(flow)
    flow_llp = util.filter(flow - max(flow), llp_taps)[::dec] + max(flow)

    # llpd, coeff = gage_fit(hirate[:,0], hirate[:,1])
    # llpd = llpd[::dec]
    times = arange(len(bandpass)) * .005 
    pylab.figure(1)
    ax = pylab.subplot(311)
    pylab.ylabel('Gage')
    pylab.plot(times + n_tap * dt/2., gage)
    pylab.plot(times, lpd)
    pylab.plot(times, llpd)

    # N = len(hirate)
    # A = ones((N, 2))
    # A[:,1] = hirate[:,3]
    # a0, a1 = dot(linalg.inv(dot(A.T, A)), dot(A.T, hirate[:,1]))
    pylab.subplot(312, sharex=ax)
    pylab.ylabel('Band Pass')
    pylab.plot(times, bandpass)
    pylab.plot(times[peaks], bandpass[peaks], peak_marker)
    pylab.plot(times[troughs], bandpass[troughs], trough_marker)
    pylab.subplot(313, sharex=ax)
    pylab.ylabel('Deltas')
    map_idx = argmax(deltas)
    pylab.plot(times[peaks] - times[peaks][map_idx], deltas)
    # gage_fit, gage_coeff, flow_fit, compl = cuff_compliance.cuff_compliance(times[skip:], llpd[skip:], flow[skip:], plot_it=True)
    #gage_fit, gage_coeff, flow_fit, compl = cuff_compliance.cuff_compliance(times[skip:], llpd[skip:], flow[skip:], plot_it=True,
    #                                                                        gage_upper_limit=1000,
    #                                                                        gage_lower_limit=20)
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run EnDys collection with arbitrary hold')
    parser.add_argument('filename', help="Output filename")
    parser.add_argument('hold_sec', help="Hold seconds", default=60, type=int)
    args = parser.parse_args()
    fn = args.filename
    hold_sec = args.hold_sec
    normal = fn + '_N.uct'
    hyper = fn + '_H.uct'
    if not os.path.exists(normal):
        endys_run(normal, 0)
        endys_run(hyper, hold_sec)
    my_plot(normal, 'bo', 'ro')
    my_plot(hyper, 'go', 'mo')
    pylab.show()
