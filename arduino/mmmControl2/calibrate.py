from drive import *
import pickle
from pylab import *
from numpy import *

p_max = 280
p_min = 30

def extract(data):
    gage = array([l[1] for l in data])
    gage = gage[argmax(gage):]
    gage = gage[:argmin(diff(gage))]
    count = mmhg_to_count(gage)
    return count

def get_pressure(data):
    n = len(data)
    slope = float(p_max - p_min) / n
    return p_max - slope * arange(n)

def linfit(x, y):
    n = len(x)
    A = ones((n, 2))
    A[:,1] = x
    return dot(linalg.inv(dot(A.T, A)), dot(A.T, y))

data1 = extract(pickle.load(open('test1')))
data2 = extract(pickle.load(open('test2')))
data3 = extract(pickle.load(open('test3')))

n1 = len(data1)
n2 = len(data2)
n3 = len(data3)

p1 = get_pressure(data1)
p2 = get_pressure(data2)
p3 = get_pressure(data3)

data = zeros((n1 + n2 + n3))
p = zeros((n1 + n2 + n3))

data[:n1] = data1
data[n1:n1 + n2] = data2
data[n1 + n2:] = data3

p[:n1] = p1
p[n1:n1 + n2] = p2
p[n1 + n2:] = p3

l = linfit(p, data)

plot(p1, data1, 'b-')
plot(p2, data2, 'g-')
plot(p3, data3, 'r-')
plot(p, l[0] + l[1] * p, 'm-')
print l
show()


