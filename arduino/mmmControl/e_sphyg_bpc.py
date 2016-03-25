import util
import pickle
from pylab import *
from numpy import *

def argcrop(raw):
    # plot(raw)
    start = argmax(raw)
    # plot(start, raw[start], 'ro')
    stop = argmin(diff(raw[start:])) + start
    # plot(stop, raw[stop], 'bo')
    return start, stop

def crop(raw):
    start, stop = argcrop(raw)
    return raw[start:stop]

def main(filename):
    raw = array(pickle.load(open(filename)))[:,1]
    raw = crop(raw)
    bp = util.blood_pressure(raw)
    return bp
    # show()
    
if __name__ == '__main__':
    deltas = []
    for fn in sys.argv[1:]:
        e_sphyg = fn.split('.')[0].split('_')[2:]
        e_sphyg = array(map(int, e_sphyg))
        try:
            mmm_sys, mmm_dia, mmm_mad_failed = main(fn)
        except Exception, e:
            print 'Error processing file %s\n    %s' % (fn, e)
            mmm_mad_failed = True
        if mmm_mad_failed == 0:
            delta = array([mmm_sys, mmm_dia]) - e_sphyg
            deltas.append(delta)
            print e_sphyg, mmm_sys, mmm_dia, delta
    deltas = array(deltas)
    mu = mean(deltas, axis=0)
    stdev = util.sample_std(deltas[:,0]), util.sample_std(deltas[:,1]), 
    N = len(deltas)
    print '        mean:', mu
    print 'standard dev:', stdev
    print '           N:', N
    ax = subplot(211)
    title("N:%d, mean: (%.2f/%.2f), sdt: (%.3f/%.3f)" % (N, mu[0], mu[1], 
                                                         stdev[0], stdev[1]))
    plot(deltas[:,0], 'bo')
    plot([0, N], [mu[0], mu[0]], 'b-')
    plot([0, N], [mu[0] + stdev[0], mu[0] + stdev[0]], 'b--')
    plot([0, N], [mu[0] - stdev[0], mu[0] - stdev[0]], 'b--')
    ylabel('Sysstolic Deltas')

    subplot(212, sharex=ax)
    plot(deltas[:,1], 'go')
    plot([0, N], [mu[1], mu[1]], 'g-')
    plot([0, N], [mu[1] + stdev[1], mu[1] + stdev[1]], 'g--')
    plot([0, N], [mu[1] - stdev[1], mu[1] - stdev[1]], 'g--')
    ylabel('Diastolic Deltas')
    xlabel("Trial")
    show()
