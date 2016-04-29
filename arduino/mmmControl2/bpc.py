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

def bpc_collect(name, listener, ucontrol, abort=None):
# if __name__ == '__main__':
    if True:
        max_p = 200
        min_p = 30
        ucontrol.maintain(0, max_p, 0, abort=abort)
        ucontrol.hirate = []
        ucontrol.record(True)
        ucontrol.deflate(min_p)
        data = ucontrol.hirate[:]
        if name is not None:
            pickle.dump(data, open(name, 'w'))
    elif False:
        try:
            ucontrol.hirate = []
            ucontrol.record(True)
            while 1:
                ucontrol.delay(1)
        except KeyboardInterrupt:
            data = ucontrol.hirate[:]
            if name is not None:
                pickle.dump(data, open(name, 'w'))
    else:
        data = pickle.load(open(name))
    return data
def bpc_process(data, listener, ucontrol):
    raw = array(data)[:,1]
    lp = filter(raw, LP_TAPS)[1000:]
    llp = filter(raw, LLP_TAPS)[1000:]
    bpf = lp - llp
    plot(bpf)
    troughs, peaks, deltas = get_troughs_peaks_deltas(bpf)
    hills = []
    for trough, peak in zip(troughs, peaks): ## filter loong pulses
        if (peak - trough) * defaults['dt'] < MAX_PULSE:
            hills.append((trough, peak))
    assert len(peaks) == len(troughs)
    hills = array(hills)
    troughs = hills[:,0]
    peaks = hills[:,1]
    
    delta_vs = []
    deltav_ps = []
    deltav_ts = []
    cuff_pressures = []

    cuff_pressures = (llp[peaks] + llp[troughs])/2.
    
    ### anomoly check using MAD
    ddeltas = diff(deltas)
    mad_thresh = defaults['mad_thresh']
    mad_n_bad_thresh = defaults['mad_n_bad_thresh']
    mad_failed = mad_thresh_test(ddeltas, mad_thresh, mad_n_bad_thresh)
    if mad_failed:
        # raise ValueError("!!! Artifact detected !!!")
        print "!!! Artifact detected !!!"
        
    figure(123)
    subplot(211)
    pid = 'MMF'
    tid = '001'
    pid_tid = '%s_%s' % (pid, tid)
    title('%s: %s MAD Test' % (pid_tid, ['Passed', 'Failed'][mad_failed] ))
    plot(deltas)
    ylabel('Deltas')
    xlabel('Time')
    subplot(212)
    ylabel('DDeltas')
    xlabel('Time')
    m = mad(ddeltas)
    plot(peaks[:-1] * defaults['dt'], ddeltas / m)
    plot([0, peaks[-1] * defaults['dt']],
         [mad_thresh, mad_thresh], 'r--')
    plot([0, peaks[-1] * defaults['dt']],
         [-mad_thresh, -mad_thresh], 'r--')
    candidate_deltas = [d for idx, d in zip(peaks, deltas) if llp[idx] > 60] ## MAP must be above 60mmhg.
    n_peak = argmax(candidate_deltas) * 2 + 1
    if n_peak >= len(peaks):
        n_peak = len(peaks)
    # n_peak = argmax(bpf[peaks] - bpf[troughs]) * 3
    if n_peak < 15:
        if len(peaks) < 15:
            n_peak = len(peaks)
        else:
            n_peak = 15
    assert n_peak <= len(peaks)
    deltas = bpf[peaks] - bpf[troughs]
    idx = arange(len(deltas))
    # plot(idx, deltas)
    delta_vs = array(delta_vs)
    max_delta_i = argmax(deltas)

    fit_idx = arange(troughs[0], troughs[n_peak-1], 1)
    fit_times = fit_idx * defaults['dt']
    p6 = poly_fit(troughs[:n_peak] * defaults['dt'], deltas[:n_peak], 6) ### Actual
    print p6
    MAP_ii = argmax(deltas)
    MAP_i = hills[MAP_ii][1]
    # MAP = llp[MAP_i]

    figure(620, figsize=(8, 4.8))
    ax = subplot(311)
    ylabel('Gage mmHG')
    plot(arange(len(bpf)) * defaults['dt'], lp)
    plot(arange(len(bpf)) * defaults['dt'], llp)

    subplot(313, sharex=ax)
    ylabel('Bandpass mmHG')
    plot(arange(len(bpf)) * defaults['dt'], bpf)
    plot(peaks * defaults['dt'], bpf[peaks], 'ro')
    plot(troughs * defaults['dt'], bpf[troughs], 'bo')
    subplot(312, sharex=ax)
    ylabel('Deltas mmHG')
    xlabel('Time Seconds')
    plot(peaks  * defaults['dt'], deltas)
    plot(peaks[:n_peak] * defaults['dt'], deltas[:n_peak], 'bd')
    print 'len(peaks)', len(peaks)
    ylim(0, 6)
    p5 = poly_der(p6)
    # map_time = find_zero(p5, hills[MAP_ii][1] * defaults['dt'])
    assert n_peak <= len(peaks), 'n_peaks > len(peaks)'
    t = arange(peaks[0] * defaults['dt'], peaks[n_peak - 1] * defaults['dt'], .05)
    y = poly_eval(p6, t)
    map_time = t[argmax(y)]
    plot([map_time], [max(y)], 'ro')
    # t = arange(0, 3 * map_time, .1)
    # y = poly_eval(p6, t)
    plot(t, y, 'r-')
    map_idx = int(map_time / defaults['dt'])
    MAP6 = llp[map_idx]

    peak_fit = poly_eval(p6, map_time)
    sbp_target = .55 * peak_fit
    dbp_target = .85 * peak_fit
    plot([map_time, map_time], [0, poly_eval(p6, map_time)], 'r--')
    plot([0, t[-1]], [dbp_target, dbp_target], 'r--')
    plot([0, t[-1]], [sbp_target, sbp_target], 'r--')

    #### find SBP time
    t = arange(map_time, 0, -.01) ### time going backwards from MAP
    pt = poly_eval(p6, t) - sbp_target
    sbp_time = t[where(pt < 0)[0][0]]

    #### find DBP time
    t = arange(map_time, 30 * map_time, .01)
    pt = poly_eval(p6, t) - dbp_target
    below_target_dbp = where(pt < 0)[0]
    if len(below_target_dbp) == 0:
        raise ValueError('target diastolic polynomial ratio not reached in polynomial evaluation')
    dbp_time = t[where(pt < 0)[0][0]]

    plot([dbp_time, dbp_time], [0, dbp_target], 'r--')
    plot([sbp_time, sbp_time], [0, sbp_target], 'r--')

    # assert sbp_time < map_time, 'sbp_time = %s > %s = MAP' % (sbp_time, map_time)
    # assert map_time < dbp_time, 'dbp_time = %s < %s = MAP' % (dbp_time, map_time)

    sbp_idx = int(sbp_time / defaults['dt'])
    dbp_idx = int(dbp_time / defaults['dt'])

    __SBP = llp[sbp_idx]
    __DBP = llp[dbp_idx]
    figure(620)
    subplot(311)
    plot([sbp_idx * defaults['dt'], sbp_idx * defaults['dt']],
         [0, __SBP], 'r--')
    plot([dbp_idx * defaults['dt'], dbp_idx * defaults['dt']],
         [0, __DBP], 'r--')
    plot([0, sbp_time], [llp[sbp_idx], llp[sbp_idx]], 'r--')
    plot([0, dbp_time], [llp[dbp_idx], llp[dbp_idx]], 'r--')
    try:
        directory = '.'
        image_number = len(glob(os.path.join(directory, "derived_BP*.png")))
        d_bp_fn = os.path.join(directory, '%s_%s_derived_BP.png' % (pid_tid, image_number))
        mad10_fn = os.path.join(directory, '%s_%s_MAD10.png' % (pid_tid, image_number))
        figure(620); subplot(311); # title('%s: %d/%d'  % (pid_tid, __SBP, __DBP))
        savefig(d_bp_fn)
        figure(123)
        savefig(mad10_fn)
        print 'wrote', d_bp_fn
        print 'wrote', mad10_fn
    except NameError:
        raise
        pass
    return __SBP, __DBP

def main(name, listener, ucontrol, abort=None):
    data = bpc_collect(name, listener, ucontrol, abort=abort)
    sys, dia = bpc_process(data, listener, ucontrol)
    print sys, dia
    return sys, dia
   
USAGE = 'python record_data.py basename'
if __name__ == '__main__':
    import sys
    listener = Listener()
    ucontrol = uControl(listener)
    main(sys.argv[1], listener, ucontrol)
