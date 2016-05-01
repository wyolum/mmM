import pickle
from util import *
import time
from drive import *
import pickle
from pylab import *
from numpy import *
from uControl import uControl

## Filter taps
dt = defaults['dt']
LP_TAPS = get_lowpass_taps(defaults['high_cuttoff_hz'], 
                                dt,
                                defaults['n_tap'])
LLP_TAPS = get_lowpass_taps(defaults['low_cuttoff_hz'], 
                                 dt,
                                 defaults['n_tap'])
DELAY_TAPS = zeros(defaults['n_tap'])
DELAY_TAPS[defaults['n_tap'] // 2] = 1

class Listener:
    '''
    Handle messages from uControl
    '''
    count = 0
    def mpid_cb(self, ucontrol, pkt):
        self.last_mpid = pkt
        if self.count % 200 == 0:
            print self.count / 200., pkt.cuff, pkt.flow, pkt.pulse
        # ucontrol.cuff = pkt.cuff
        self.count += 1
        # ucontrol.abort()
    def lpid_cb(self, ucontro, pkt):
        self.last_lpid = pkt
    def status_cb(self, ucontrol, pkt):
        self.last_status = pkt
    def short_cb(self, ucontrol, pkt):
        self.last_short = pkt


def main(name, listener, ucontrol):
    min_p = 30
    max_p = 200
           # pressure, hold, fast, hold
           #  0            1     2    3
    runs = [
        (min_p + 30,   0,  True, 30),
        (max_p     ,   0, False, 30),   # Slow
        (max_p     ,   0, True, 30),    # Fast
        (max_p     , 300, False, 30),   ## slow release
        (max_p     ,   0,  True, 30)     ## fast
    ]
    
    def bleed_abort():
        if ucontrol.lpf.last > min_p + 5:
            ucontrol.deflate(min_p + 4, fast = False)
        return False

    for i, run in enumerate(runs):
        print 'PROTO:: inflate'
        ucontrol.maintain(0, run[0], run[1], abort=None) ## inflate
        print 'PROTO:: record'
        ucontrol.hirate = []                                       ## start recording
        ucontrol.record(True)
        print 'PROTO:: deflate, fast=', run[2]
        ucontrol.deflate(min_p + 5, run[2])                        ## deflate 
        print 'PROTO:: hold'
        ucontrol.maintain(0, min_p + 5, run[3], abort=bleed_abort)                ## hold
        fn = '%s_%02d.dat' %(name, i)                     
        pickle.dump(ucontrol.hirate, open(fn, 'w'))                ## save
        print 'wrote', fn
USAGE = 'python record_data.py basename'
if __name__ == '__main__':
    import sys
    listener = Listener()
    ucontrol = uControl(listener)
    main(sys.argv[1], listener, ucontrol)
