import e_sphyg_bpc
from constants import *
import os.path
import glob
from util import *
from pylab import *
from numpy import *
import pickle

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


def ideal_gas_compliance(gage_p, v0):
    return v0 / (gage_p + 760.)

def main(filename):
    fn = filename
    data = array(pickle.load(open(fn)))
    times = data[:,0] / 1000.
    dt = median(diff(times)) 

    start, stop = e_sphyg_bpc.argcrop(data[:,1])
    croptimes = data[start:stop,0]/1000.
    my_times = data[start, 0] + arange(stop - start) * dt

    cropped = data[start:stop,1]
    lp = filter(cropped - cropped[0], LP_TAPS) + cropped[0]
    llp = filter(cropped - cropped[0], LLP_TAPS) + cropped[0]
    bpf = lp - llp

    t, p, d = get_troughs_peaks_deltas(bpf[750:])
    t += 750
    p += 750

    fit_idx = t
    n_peak = len(t)
    fit_times = fit_idx * dt
    p6 = poly_fit(t * dt, d, 6) ### Actual
    p5 = poly_der(p6)
    tm = numpy.arange(p[0] * dt, p[n_peak - 1] * dt, dt)
    y = poly_eval(p6, tm)
    maxy = max(y)
    sys_i = where(y > .55 * maxy)[0][0]
    dia_i = where(y > .85 * maxy)[0][-1]
    sys_i = int(tm[sys_i]/dt)
    dia_i = int(tm[dia_i]/dt)
    sys = llp[sys_i]
    dia= llp[dia_i]

    ax = subplot(311)
    title(fn)
    plot(times - start * dt, data[:,1], 'r-')
    plot(croptimes - start * dt, cropped, 'b-')
    ylabel('mmHG')
    plot(arange(len(lp)) * dt, lp)
    plot([0., times[sys_i]], [sys, sys], 'r--')
    plot([times[sys_i], times[sys_i]], [0, sys], 'r--')
    plot([0, times[dia_i]], [dia, dia], 'g--')
    plot([times[dia_i], times[dia_i]], [0, dia], 'g--')
    
    sys, dia, pf = blood_pressure(cropped)
    plot([0, times[sys_i]], [sys, sys], 'rx')
    plot([0, times[dia_i]], [dia, dia], 'gx')

    text(1, sys, '%.2f' % sys)
    text(1, dia, '%.2f' % dia)

    subplot(312, sharex=ax)
    ylabel('Band Pass')
    plot(arange(len(bpf)) * dt, bpf, 'b-')
    plot(t * dt, bpf[t], 'bo')
    plot(p * dt, bpf[p], 'bo')
    lo, hi = ylim()
    plot([times[sys_i], times[sys_i]], [lo, hi], 'r--')
    plot([times[dia_i], times[dia_i]], [lo, hi], 'g--')

    subplot(313, sharex=ax)
    ylabel('%-Deltas')
    plot(t * dt, 100 * d / maxy, 'bo')

    plot(tm, 100 * y / maxy)

    lo, hi = 0, 110
    plot([times[sys_i], times[sys_i]], [55, hi], 'r--')
    plot([0, times[sys_i]], [55, 55], 'r--')
    plot([times[sys_i]], [55], 'rx')
    text(1, 55, '55%')
    plot([times[dia_i], times[dia_i]], [85, hi], 'g--')
    plot([0, times[dia_i]], [85, 85], 'g--')
    plot([times[dia_i]], [85], 'gx')
    text(1, 85, '85%')

    plot([times[sys_i], times[sys_i]], [55, 2.5*hi], 'r--', clip_on=False)
    plot([times[dia_i], times[dia_i]], [85, 2.5*hi], 'g--', clip_on=False)


    xlim(0)
    ylim(0, hi)
    return sys, dia

class Usage(Exception):
    def __repr__(self):
        return 'python %s filename' % os.path.split(__file__)[1]

USAGE = Usage()
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        raise USAGE
    fn = sys.argv[1]
    print '%.2f/%.2f' % main(fn)
    show()
