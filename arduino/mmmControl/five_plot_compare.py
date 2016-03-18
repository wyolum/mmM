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

base = 'michael_2'
base = 'justin_2'

def main(base, regression_file = None):
    fn1 = '%s_no_release_base.uct' % base
    fn2 = '%s_fast_release_base.uct' % base
    fn3 = '%s_slow_release_base.uct' % base
    fn4 = '%s_fast_release_hyper.uct' % base
    fn5 = '%s_slow_release_hyper.uct' % base


    data1 = array(pickle.load(open(fn1)))
    data2 = array(pickle.load(open(fn2)))
    data3 = array(pickle.load(open(fn3)))
    data4 = array(pickle.load(open(fn4)))
    data5 = array(pickle.load(open(fn5)))
    
    if True:
        datas = [data1, data2, data3, data4, data5]
        colors = 'bgrcm'
        figure()
        for i, data in enumerate(datas):
            color = colors[i]
            plot(data[:,0] / 1000/60., data[:,1], '%s-' % color)                
            
        xlabel('Time Minutes')
        ylabel('Gage pressure mmHG')
        fn = '%s_abs_time.png' % base
        savefig(fn)
        print 'wrote', fn
        
    if True:
        data1 = data1[data1[:,1] < 35]
        data2 = data2[data2[:,1] < 35]
        data3 = data3[data3[:,1] < 35]
        data4 = data4[data4[:,1] < 35]
        data5 = data5[data5[:,1] < 35]
    
    lp1 = filter(data1[:,1], LP_TAPS)[1000:]
    llp1 = filter(data1[:,1], LLP_TAPS)[1000:]
    bpf1 = lp1 - llp1

    lp2 = filter(data2[:,1], LP_TAPS)[1000:]
    llp2 = filter(data2[:,1], LLP_TAPS)[1000:]
    bpf2 = lp2 - llp2

    lp3 = filter(data3[:,1], LP_TAPS)[1000:]
    llp3 = filter(data3[:,1], LLP_TAPS)[1000:]
    bpf3 = lp3 - llp3

    lp4 = filter(data4[:,1], LP_TAPS)[1000:]
    llp4 = filter(data4[:,1], LLP_TAPS)[1000:]
    bpf4 = lp4 - llp4

    lp5 = filter(data5[:,1], LP_TAPS)[1000:]
    llp5 = filter(data5[:,1], LLP_TAPS)[1000:]
    bpf5 = lp5 - llp5

    t1, p1, d1 = get_troughs_peaks_deltas(bpf1)
    t2, p2, d2 = get_troughs_peaks_deltas(bpf2)
    t3, p3, d3 = get_troughs_peaks_deltas(bpf3)
    t4, p4, d4 = get_troughs_peaks_deltas(bpf4)
    t5, p5, d5 = get_troughs_peaks_deltas(bpf5)

    for set_i, (ti, pi, di, llpi) in enumerate([[t1, p1, d1, llp1],
                                                [t2, p2, d2, llp2],
                                                [t3, p3, d3, llp3],
                                                [t4, p4, d4, llp4],
                                                [t5, p5, d5, llp5]]):
        if(regression_file is not None):
            for j in range(len(di)):
                line = (base, set_i + 1, llpi[pi[j]], di[j])
                print >> regression_file, ','.join(map(str, line))

    figure()
    subplot(211)
    plot(bpf3, 'r-')
    plot(t3, bpf3[t3], 'ro')
    plot(p3, bpf3[p3], 'ro')
    subplot(212)
    plot(bpf3, 'r-')
    figure()
    n = len(bpf3)
    plot(1/rfftfreq(n, dt), abs(rfft(bpf3)))
    # show()
    
    if False:
        figure()
        plot(bpf1, 'b-')
        plot(t1, bpf1[t1], 'bo')
        plot(p1, bpf1[p1], 'bo')

        plot(bpf2, 'g-')
        plot(t2, bpf2[t2], 'go')
        plot(p2, bpf2[p2], 'go')

        plot(bpf3, 'r-')
        plot(t3, bpf3[t3], 'ro')
        plot(p3, bpf3[p3], 'ro')

        plot(bpf4, 'r-')
        plot(t4, bpf4[t4], 'co')
        plot(p4, bpf4[p4], 'co')

        plot(bpf5, 'r-')
        plot(t5, bpf5[t5], 'mo')
        plot(p5, bpf5[p5], 'mo')

    figure()
    y = ones(len(d1)) * mean(d1); plot(llp1[t1], y, 'b-', linewidth=3)
    x = ones(len(d1)) * mean(llp1[t1]); plot(x, d1, 'b-', linewidth=3)
    plot(llp1[t1], d1, 'bo')

    y = ones(len(d2)) * mean(d2); plot(llp2[t2], y, 'g-', linewidth=3)
    x = ones(len(d2)) * mean(llp2[t2]); plot(x, d2, 'g-', linewidth=3)
    plot(llp2[t2], d2, 'go')

    y = ones(len(d3)) * mean(d3); plot(llp3[t3], y, 'r-', linewidth=3)
    x = ones(len(d3)) * mean(llp3[t3]); plot(x, d3, 'r-', linewidth=3)
    plot(llp3[t3], d3, 'ro')

    y = ones(len(d4)) * mean(d4); plot(llp4[t4], y, 'c-', linewidth=3)
    x = ones(len(d4)) * mean(llp4[t4]); plot(x, d4, 'c-', linewidth=3)
    plot(llp4[t4], d4, 'co')

    y = ones(len(d5)) * mean(d5); plot(llp5[t5], y, 'm-', linewidth=3)
    x = ones(len(d5)) * mean(llp5[t5]); plot(x, d5, 'm-', linewidth=3)
    plot(llp5[t5], d5, 'mo')
    
    xlabel('Gage Pressure mmHG')
    ylabel('Pulse Pressure Delta mmHG')
    title(base)
    fn = '%s.png' % base
    savefig(fn)
    print 'wrote', fn
    figure()
    plot((p1 - p1[0]) * dt, d1, 'bo')
    plot((p2 - p2[0]) * dt, d2, 'go')
    plot((p3 - p3[0]) * dt, d3, 'ro')
    plot((p4 - p4[0]) * dt, d4, 'co')
    plot((p5 - p5[0]) * dt, d5, 'mo')
    xlabel('Time from hold start (sec)')
    ylabel('Delta mmHG')
    title(base)
    fn = '%s_vs_time.png' % base
    savefig(fn)
    print 'wrote', fn
    return
    show()

class Usage(Exception):
    def __repr__(self):
        return 'python compare_data.py base_name'

def runall():
    pattern = '*slow_release_base.uct'
    files = glob.glob(pattern)
    regression_file = open('regression.csv', 'w')
    for file in files:
        base = file[:-len(pattern)]
        main(base, regression_file = regression_file)
        close('all')
# runall();here
USAGE = Usage()
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        raise USAGE
    base = sys.argv[1]
    main(base)
    show()
