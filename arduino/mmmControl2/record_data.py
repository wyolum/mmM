import util
import e_sphyg_bpc
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
    def mpid_cb(self, pkt):
        self.last_mpid = pkt
        if self.count % 200 == 0:
            print self.count / 200., pkt.cuff, pkt.flow
        # ucontrol.cuff = pkt.cuff
        self.count += 1
        # ucontrol.abort()
    def lpid_cb(self, pkt):
        self.last_lpid = pkt
    def status_cb(self, ucontrol, pkt):
        self.last_status = pkt
    def short_cb(self, pkt):
        self.last_short = pkt

listener = Listener()
ucontrol = uControl(listener)

def main(base):
    try:
        ucontrol.hirate = []
        ucontrol.record(True)
        while True:
            ucontrol.delay(1)
    except KeyboardInterrupt:
        data = ucontrol.hirate[:]
        raw = [l[1] for l in data]
        raw = e_sphyg_bpc.crop(raw)
        print util.blood_pressure(raw)
        show()
    finally:
        ext = raw_input('sys_dia:')
        pickle.dump(data, open('%s_%s.uct' % (base, ext), 'w'))
        ucontrol.abort()

USAGE = 'python record_data.py basename'
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        raise USAGE
    base = sys.argv[1]
    main(base)
