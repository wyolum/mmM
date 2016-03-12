import time
from drive import *
import pickle
from pylab import *
from numpy import *
from uControl import uControl

class Listener:
    '''
    Handle messages from uControl
    '''
    count = 0
    def mpid_cb(self, ucontrol, pkt):
        self.last_mpid = pkt
        if self.count % 200 == 0:
            print self.count / 200., pkt.cuff, pkt.flow
        # ucontrol.cuff = pkt.cuff
        self.count += 1
        # ucontrol.abort()
    def lpid_cb(self, ucontro, pkt):
        self.last_lpid = pkt
    def status_cb(self, ucontrol, pkt):
        self.last_status = pkt
    def short_cb(self, ucontrol, pkt):
        self.last_short = pkt

def collect(max_p, hold_p, hold_t):
    ucontrol.maintain(0, max_p, 0)
    ucontrol.hirate = []
    ucontrol.record(True)
    ucontrol.deflate(hold_p)
    ucontrol.delay(hold_t)
    data = ucontrol.hirate[:]
    return data

listener = Listener()
ucontrol = uControl(listener)

def main(base):
# if __name__ == '__main__':
    # base = 'justin_1'
    #base = 'michael_2'

    duration = 30
    # do no release baseline
    c1 = collect(50, 30, duration)
    pfn = '%s_no_release_base.uct' % base
    pickle.dump(c1, open(pfn, 'w'))
    print 'wrote', pfn

    # do fast release baseline
    ucontrol.maintain(0, 190, 0) ### pump it up
    print 'manual release down to 0'
    ucontrol.deflate(10)
    while ucontrol.cuff_pressure > 10:
        ucontrol.delay(.5)
    c2 = collect(50, 30, duration)
    pfn = '%s_fast_release_base.uct' % base
    pickle.dump(c2, open(pfn, 'w'))
    
    # do slow release baseline
    c3 = collect(190, 30, duration)
    pfn = '%s_slow_release_base.uct' % base
    pickle.dump(c3, open(pfn, 'w'))
    
    # do fast release hyper
    ucontrol.maintain(180, 190, 300) ### pump it up and hold
    print 'manual release down to 0'
    ucontrol.deflate(10)
    while ucontrol.cuff_pressure > 10:
        ucontrol.delay(.5)
    c4 = collect(50, 30, duration)
    pfn = '%s_fast_release_hyper.uct' % base
    pickle.dump(c4, open(pfn, 'w'))

    # do slow release hyper
    c5 = collect(190, 30, duration)
    pfn = '%s_slow_release_hyper.uct' % base
    pickle.dump(c5, open(pfn, 'w'))
    print 'wrote', pfn
    ucontrol.abort()

USAGE = 'python record_data.py basename'
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        raise USAGE
    base = sys.argv[1]
    main(base)
