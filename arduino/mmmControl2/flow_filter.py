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

data = array(pickle.load(open('justin_1.dat')))
pres = data[:,1]
flow = data[:,2]
llp_pres = filter(pres - pres[0], LLP_TAPS) + pres[0]
llp_flow = filter(flow - flow[0], LLP_TAPS) + flow[0]

plot(pres, flow)
plot(llp_pres, llp_flow)
show()
