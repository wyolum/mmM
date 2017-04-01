from numpy import *
from pylab import *
import struct

OFFSET = 1636.12
VOL = 140.

fn = sys.argv[1]
dat = open(fn).read()
raw_dat = array(struct.unpack('%dl' % (len(dat)//8), dat)).reshape((-1, 2))


dat = raw_dat.astype(float)
dat[:,1] -= OFFSET
keep = dat[:,1] > 0
keep = logical_and(keep, dat[:,1] < 10000)
toss = logical_not(keep)
dat[toss, 1] = 0

figure()
ax = subplot(211)
plot(dat[:,1])


start_stops = [
    [1070, 4138],
    [4870, 6396],
    [6965, 8206],
    [8724, 9663],
    [10116, 10877]
]


factors = []
for start, stop in start_stops:
    fill([start, start, stop, stop],
         [0, 3000, 3000, 0],
         alpha=.3)
    dt = 1./200.
    vol = sum(dat[start:stop,1]) * dt
    factor = vol / VOL
    print 'factor', factor
    factors.append(factor)
factor = 1./mean(factors)
factor = 0.02179666666666667
OFFSET = 1638.
print 'mean factor', factor
subplot(212, sharex=ax)
dat[:,1] *= factor
plot(dat[:,1])
plot((raw_dat[:,1] - OFFSET) * factor)
print OFFSET, factor
for start, stop in start_stops:
    fill([start, start, stop, stop],
         [0, 100, 100, 0],
         alpha=.3)
    dt = 1./200.
    vol = sum((dat[start:stop,1])) * dt
    print 'computed vol', vol
    text(start, 100, '%.1f' % vol)
show()
