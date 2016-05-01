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
    files = glob.glob("%s_[0-9][0-9].dat" % base)
    files.sort()
    datas = [array(pickle.load(open(file))) for file in files]
    colors = 'bgrcm'
    for i, data in enumerate(datas):
        color = colors[i]
        figure(1)
        title('Raw')
        plot(data[:,0] / 1000/60., data[:,1], '%s-' % color)                
        xlabel('Time Minutes')
        ylabel('Gage pressure mmHG')

        data = data[data[:,1] < 55]
        lp = filter(data[:,1], LP_TAPS)[1000:]
        llp = filter(data[:,1], LLP_TAPS)[1000:]
        bpf = lp - llp
        try:
            figure(2)
            title('Band Pass')
            plot(bpf, '%s-' % color)
            t, p, d = get_troughs_peaks_deltas(bpf)
            plot(t, bpf[t], '%so' % color)
            plot(p, bpf[p], '%so' % color)
        except:
            close('all')
            plot(bpf)
            show()
            pass
        
        
        figure(3)
        keep = d < 5
        plot(t[keep], d[keep], '%s-' % color, linewidth=3, label=str(i + 1))
        if base.endswith('03'):
            title(base + ', Slow first')
        else:
            title(base + ', Fast first')
        legend(loc='best')

        figure(4)
        title('Flow')
        plot(data[:,0], data[:,3])
        continue
        figure(4)
        n = len(bpf)
        plot(1/rfftfreq(n, dt), abs(rfft(bpf)), '%s-' % color)
        show()
    figure(1)
    fn = '%s_abs_time.png' % base
    savefig(fn)
    print 'wrote', fn
    
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
