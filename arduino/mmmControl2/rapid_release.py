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

def collect(name, listener, ucontrol, hold=0, fast_deflate=False, abort=None, min_p=30, max_p=200):
# if __name__ == '__main__':
    
    ucontrol.maintain(0, max_p, hold, abort=abort)
    ucontrol.hirate = []
    ucontrol.record(True)
    ucontrol.deflate(min_p, fast=fast_deflate)
    ucontrol.maintain(0, min_p, 30, abort=abort)
     
    data = ucontrol.hirate[:]
    if name is not None:
        pickle.dump(data, open(name, 'w'))
    return data

def main(name, listener, ucontrol, abort=None):
    min_p = 30
    max_p = 200
           # pressure, hold, fast, hold
           #  0            1     2    3
    runs = [(min_p + 30,   0,  True, 30),
            (max_p     ,   0,  True, 30),
            (max_p     ,   0, False, 30),
            (max_p     , 300,  True, 30),
            (max_p     ,   0, False, 30)]
    
    for i, run in enumerate(runs):
        ucontrol.maintain(0, run[0], run[1], abort=abort) ## inflate
        ucontrol.hirate = []                              ## start recording
        ucontrol.record(True)
        ucontrol.deflate(min_p, run[2])                   ## deflate 
        ucontrol.maintain(0, min_p, run[3])               ## hold
        fn = '%s_%02d.dat' %(name, i)                     
        pickle.dump(ucontrol.hirate, open(fn, 'w'))       ## save
        print 'wrote', fn
        
    ## inflate to min_p + 30
    ## hold 0
    ## fast deflate to min_p
    ## start measurements
    ## hold 30
    ## save measurements

    ## inflate to max_p
    ## hold 0
    ## start measurements
    ## slow deflate to min_p
    ## hold 30
    ## stop measurements

    ## inflate to max_p
    ## hold 0
    ## start measurements
    ## fast deflate to min_p
    ## hold 30
    ## stop measurements

    ## inflate to max_p
    ## hold 600
    ## start measurements
    ## fast deflate to min_p
    ## hold 30
    ## stop measurements

    ## inflate to max_p
    ## hold 0
    ## start measurements
    ## slow deflate to min_p
    ## hold 30
    ## stop measurements

    
    data = collect(name, listener, ucontrol, hold=3, abort=abort, fast_deflate=True)
    data = collect(name, listener, ucontrol, hold=3, abort=abort, fast_deflate=False)
    ucontrol.maintain(0, max_p, 0, abort=abort)
    ucontrol.deflate(min_p)
    
    
USAGE = 'python record_data.py basename'
if __name__ == '__main__':
    import sys
    listener = Listener()
    ucontrol = uControl(listener)
    main(sys.argv[1], listener, ucontrol)
