import pickle
import os.path
from constants import *
import warnings
import numpy
import numpy.linalg as linalg
from numpy import log10, exp, pi, sqrt, arctan2, real, imag, sin, cos, median
import scipy
from scipy import stats
from scipy import signal
from scipy import optimize
import scipy.integrate
# import bioread

import pylab
# import peakdetect

def blood_pressure(raw):
    '''
    pressure is the raw pressure readings for the descent data only
    returns sys, dia, map, hr
    '''
    dt = defaults['dt']
    lp = filter(raw, LP_TAPS)[1000:]
    llp = filter(raw, LLP_TAPS)[1000:]
    bpf = lp - llp
    # pylab.plot(bpf); pylab.show()
    troughs, peaks, deltas, pulse_period = get_troughs_peaks_deltas(bpf)
    
    delta_vs = []
    deltav_ps = []
    deltav_ts = []
    cuff_pressures = (llp[peaks] + llp[troughs])/2.
    
    ### anomoly check using MAD
    ddeltas = numpy.diff(deltas)
    mad_thresh = defaults['mad_thresh']
    mad_n_bad_thresh = defaults['mad_n_bad_thresh']
    mad_failed = mad_thresh_test(ddeltas, mad_thresh, mad_n_bad_thresh)
    if mad_failed:
        raise ValueError("Motion Detected")
        print "!!! Artifact detected !!!"
        
    candidate_deltas = [d for idx, d in zip(peaks, deltas) if llp[idx] > 60] ## MAP must be above 60mmhg.
    n_peak = numpy.argmax(candidate_deltas) * 2 + 1
    if n_peak >= len(peaks):
        n_peak = len(peaks)
    if n_peak < 15:
        if len(peaks) < 15:
            n_peak = len(peaks)
        else:
            n_peak = 15
    assert n_peak <= len(peaks)
    idx = numpy.arange(len(deltas))

    fit_idx = numpy.arange(troughs[0], troughs[n_peak-1], 1)
    fit_times = fit_idx * dt
    p6 = poly_fit(troughs[:n_peak] * dt, deltas[:n_peak], 6) ### Actual
    p5 = poly_der(p6)
    t = numpy.arange(peaks[0] * dt, peaks[n_peak - 1] * dt, .05)
    y = poly_eval(p6, t)
    map_time = t[numpy.argmax(y)]
    map_idx = int(map_time / dt)
    MAP6 = llp[map_idx]

    peak_fit = poly_eval(p6, map_time)
    sbp_target = .55 * peak_fit
    dbp_target = .85 * peak_fit

    #### find SBP time
    t = numpy.arange(map_time, 0, -.01) ### time going backwards from MAP
    pt = poly_eval(p6, t) - sbp_target
    sbp_time = t[numpy.where(pt < 0)[0][0]]

    #### find DBP time
    t = numpy.arange(map_time, 30 * map_time, .01)
    pt = poly_eval(p6, t) - dbp_target
    below_target_dbp = numpy.where(pt < 0)[0]
    if len(below_target_dbp) == 0:
        raise ValueError('target diastolic polynomial ratio not reached in polynomial evaluation')
    dbp_time = t[numpy.where(pt < 0)[0][0]]

    sbp_idx = int(sbp_time / dt)
    dbp_idx = int(dbp_time / dt)

    sbp = llp[sbp_idx]
    dbp = llp[dbp_idx]
    hr = 60./pulse_period
    return sbp, dbp, MAP6, hr
    
def get_troughs_peaks_deltas(bpf):
    peaks, troughs, pulse_period = find_pulse_peaks_and_troughs(
        bpf,
        defaults['dt'],
        return_pulse_period=True)
    if peaks[0] < troughs[0]: # peak follows trough
        peaks = peaks[1:]
    if troughs[-1] > peaks[-1]: # peak follows trough
        troughs = troughs[:-1]
    hills = []
    for trough, peak in zip(troughs, peaks): ## filter loong pulses
        if (peak - trough) * defaults['dt'] < MAX_PULSE:
            hills.append((trough, peak))
    assert len(peaks) == len(troughs)
    hills = numpy.array(hills)
    troughs = hills[:,0]
    peaks = hills[:,1]
    deltas = bpf[peaks] - bpf[troughs]
    return troughs, peaks, deltas, pulse_period

def sample_std(nums):
    n = len(nums)
    nums = numpy.array(nums)
    mu = numpy.mean(nums)
    devs = nums - mu
    s = numpy.sqrt(numpy.sum(devs ** 2) / (n - 1))
    return s

assert abs(sample_std([90., 100, 110]) - 10) < 1e-8

def cv(nums):
    n = len(nums)
    nums = numpy.array(nums)
    mu = numpy.mean(nums)
    s = sample_std(nums)
    return s / mu

class uControl:
    flow_idx = 2
    gage_idx = 1
    time_idx = 0
    def __init__(self, filename):
        pickle_file = open(filename)
        dat = pickle.load(pickle_file)
        self.normal = dat['normal']
        self.normal_temp = dat['normal_temp']
        self.normal_pressure = dat['normal_pressure']
        self.normal_gage = self.normal[:,self.gage_idx]
        self.normal_flow = self.normal[:,self.flow_idx]
        self.normal_time = self.normal[:,self.time_idx]
        
        self.hyper = dat['hyper']
        self.hyper_temp = dat['hyper_temp']
        self.hyper_pressure = dat['hyper_pressure']
        self.hyper_gage = self.hyper[:,self.gage_idx]
        self.hyper_flow = self.hyper[:,self.flow_idx]
        self.hyper_time = self.hyper[:,self.time_idx]

class Empty:
    pass

class uControl2:
    '''
    new single run data files (normal or hyper)
    '''
    flow_idx = 2
    gage_idx = 1
    time_idx = 0
    def __init__(self, filename):
        pickle_file = open(filename)
        dat = pickle.load(pickle_file)
        self.temp = dat['temp']
        self.hirate = dat['hirate']
        self.pressure = dat['pressure']
        self.gage = self.hirate[:,self.gage_idx]
        self.flow = self.hirate[:,self.flow_idx]
        self.time = self.hirate[:,self.time_idx]

    def __getitem__(self, i):
        return self.hirate[i]

    def __add__(self, other):
        '''
        return old style normal + hyperemia uControl file
        '''
        out = Empty()
        out.normal = self
        out.normal_temp = self.temp
        out.normal_pressure = self.pressure
        out.normal_gage = self.hirate[:,self.gage_idx]
        out.normal_flow = self.hirate[:,self.flow_idx]
        out.normal_time = self.hirate[:,self.time_idx]

        out.hyper = other
        out.hyper_temp = other.temp
        out.hyper_pressure = other.pressure
        out.hyper_gage = other.hirate[:,other.gage_idx]
        out.hyper_flow = other.hirate[:,other.flow_idx]
        out.hyper_time = other.hirate[:,other.time_idx]
        
        return out

def mad(x):
    return median(abs(x - median(x)))

def mad_thresh_test(x, t, b):
    '''
    Compute MAD test
    Return false if MAD test fails
    x -- ddeltas
    t -- thresh (mad multiplier)
    b -- number of acceptable bad
    '''
    m = mad(x)
    # print 'median(x):', median(x)
    # print 'mad:', m

    ## check for successive mad failures.
    mad_deltas = x - median(x)
    bad = abs(mad_deltas) > t * m
    successive = numpy.diff(numpy.where(bad)[0])
    out = numpy.any(successive <= 2) or any(mad_deltas) > 2 * m * t
    # old_ans = sum(abs(x - median(x)) > t * m) > b
    return out

def get_flow(gage, cba):
    '''
    quadratic formula to find flow given gage
    '''
    c, b, a = cba
    return (-b + sqrt(b ** 2 - 4 * a * (c - gage))) / (2 * a)

def flow_of_gage(flow, gage, cba=None):
    '''
    return the quadratic smoothed flow values, and coefficients, c, b, and a, to be used on subsequent calls to save computation time
    
    pressure = a flow^2 + b flow + c
    flow -- flow measurements corrected for temp and pressure
    gage -- gage pressure measurements
    '''
    flow = numpy.array(flow)
    keep = (flow > 50)
    keep = numpy.arange(len(flow))
    __flow = flow[keep]
    __gage = numpy.array(gage)[keep]

    N = len(__flow)
    A = numpy.array(zip(numpy.ones(len(keep)), __flow, __flow ** 2))
    if cba is None:
        cba = numpy.dot(numpy.linalg.inv(numpy.dot(A.T, A)), numpy.dot(A.T, __gage))
    flow_fit = get_flow(gage, cba)

    print 'cba', cba
    return flow_fit, cba, A

def gage_of_flow(flow, cba):
    return cba[0] + cba[1] * flow + cba[2] * flow ** 2

def ideal_gas_compliance(gage_p, v0):
    return v0 / (gage_p + 760.)
        
def separate_runs(dat):
    '''
    return run1_stop, run2_start induces
    '''
    peaks, troughs = find_peaks_and_troughs(dat, 100)
    if len(troughs) != 1:
        if False:
            pylab.figure()
            pylab.plot(dat)
            if len(troughs) > 1:
                pylab.plot(troughs, dat[troughs], 'ro')
            pylab.show()
        raise ValueError('Unable to separate data into two runs')
    run1_stop = troughs[0]
    run2_start = troughs[0]
    return run1_stop, run2_start

def separate_runs__test__():
    dat = scipy.loadtxt('../input/AS_one.TXT', skiprows=1, usecols=[0])
    start, stop = separate_runs(decimate(decimate(dat[::])))
    assert start == stop == 165
    
def moving_argmax(data, N):
    '''
    Return the indexes of the maxumum point for a sliding window of length n
    '''
    inds = [numpy.argmax(data[:N])]
    vals = [data[inds[0]]]
    for i in range(N, len(data) - N + 1):
        imax = numpy.argmax(data[i:i + N])
        if imax + i not in inds:
            inds.append(imax + i)
            vals.append(data[imax + i])
    # prune inds where there is a larger within the window
    # pylab.figure(432); pylab.plot(inds, vals, 'ro')
    remove = []
    for i in inds:
        if len(data[i - N: i]) > 0 and max(data[i - N: i]) > data[i]:
            remove.append(i)
        elif len(data[i + 1: i + N]) > 0 and max(data[i + 1: i + N]) > data[i]:
            remove.append(i)
    for i in remove:
        inds.remove(i)
    # vals = []
    # for i in inds:
    #     vals.append(data[i])
    # pylab.figure(432); pylab.plot(inds, vals, 'bo')
    # pylab.show()
    return inds

def moving_argmax__test__():
    t = numpy.arange(0, 3, .01)
    data = numpy.sin(2 * pi * 5 * t) + numpy.random.random(len(t)) - .5
    idx = moving_argmax(data, 10)
    for i in idx:
        assert data[i] >= max(data[max([0, i - 10]): min([len(data), i + 10])])
moving_argmax__test__()

def integrate(ys, xs):
    return numpy.trapz(ys, xs)

def filter_deltas(idx, deltas, thresh=.5, plotit=False):
    '''
    return induces of deltas to keep
    '''
    smoothed = filter(deltas[idx], [.5, 0, .5])
    # keep first delta??
    test_data = abs(deltas[idx[:-1]] - smoothed[idx[1:]]) / smoothed[idx[1:]]
    if plotit:
        pylab.figure(999)
        pylab.subplot(211)
        pylab.plot(deltas)
        pylab.plot(smoothed)
        pylab.subplot(212)
        pylab.plot(test_data)
    while max(test_data[1:]) > thresh:
        toss = idx[numpy.argmax(test_data[1:]) + 1]
        idx = idx[idx!=toss]
        smoothed = filter(deltas[idx], [.5, 0, .5])
        test_data = abs(deltas[idx[:-1]] - smoothed[1:]) / smoothed[1:]
        if plotit:
            pylab.plot(idx[:-1], test_data)
    return idx

def GetInterpolationIndex(x, xval):
    n= len(x)
    i = -1;
    if((x[0] <= xval) and (xval <= x[n - 1])):
        for i in range(n):
            if x[i] >= xval:
                break
                # for(i = 0; (i < n) && (x[i] < xval); i++)
                #{
                #    // find i where x[i] <= xval <= x[i+1]
                #}

        i -= 1
        s = (xval - x[i]) / (x[i + 1] - x[i])
    else:
        raise ValueError("xval not in interval")
    index = i;
    frac = s;
    return index, frac;

def trapz_integral(x, y, a, b):
    '''
    integrate function y between x=a and x=b.
    trapazoidal rule for interior points, interpolate endpoints.
    '''
    from numpy import inf
    idx = numpy.argsort(x)
    y = y[idx]
    x = x[idx] ## sort data by x
    out = 0
    n = len(x)

    ### get first trapazoid
    i, s = GetInterpolationIndex(x, a)
    y1 = y[i] + s * (y[i + 1] - y[i])
    y2 = y[i + 1]
    out = (y1 + y2) * (x[i + 1] - a) / 2.

    ### get middle trapazoids (overshoot by portion of trap)
    while (i < n) and (x[i + 1] < b):
        i += 1;
        out += (y[i] + y[i + 1]) * (x[i + 1] - x[i]) / 2.


    #  overshot by a portion of a quad, subtract it off
    i, s = GetInterpolationIndex(x, b)
    y1 = y[i] + s * (y[i + 1] - y[i]);
    y2 = y[i + 1];
    out += (y1 + y2) * (b - x[i + 1]) / 2.;
    return out

def trapz_intrgral__test__():
    x = numpy.arange(10)
    y = numpy.arange(0, 20, 2)
    a = .5
    b = 4.5
    assert abs(trapz_integral(x, y, a, b) - 20) < 1e-8
trapz_intrgral__test__()

def poly_der(poly):
    return numpy.array([poly[i + 1] * (i + 1) for i in range(len(poly) - 1)])

def find_zero(poly, guess, max_iter=100, eps=1e-5):
    x0 = guess
    dydx = poly_der(poly)
    for iter in range(max_iter):
        pows = [x0 ** i for i in range(len(poly))]
        y0 = numpy.dot(poly, pows)
        slope = numpy.dot(dydx, pows[:-1])
        if abs(slope) < eps:
            raise ValueError("divide by zero in Newton's Method")
        # 0 = y0 + slope(x1 - x0)
        # -y0 = slope(x1 - x0)
        # x0 -y0 / slope = x1
        x1 = x0 - y0/slope
        if abs(x1 - x0) < eps:
            break
        x0 = x1
    else:
        pylab.show()
        raise ValueError("Optimization did not coverge")
    return x1

def poly_solve(poly, y, guess, max_iter=100, eps=1e-5):
    '''
    solve poly(x) = y for x
    '''
    coeff = poly.copy()
    coeff[0]-= y
    return find_zero(coeff, guess, max_iter, eps)
    
def poly_eval(poly, x):
    pows = [x ** i for i in range(len(poly))]
    return numpy.dot(poly, pows)

def optimize(poly, guess, max_iter=100, eps=1e-5):
    dydx = poly_der(poly)
    x = find_zero(dydx, guess, max_iter=max_iter, eps=eps)
    return x

def optimize__test__():
    assert numpy.abs(optimize([1,-2, 1], -4) - 1) < 1e-4
    assert numpy.abs(optimize([0, 0, 1], -4) - 0) < 1e-4
    poly = [-1, 1, -1]
    dydx = poly_der(poly)
    x = optimize(poly,  2.2)
    assert abs(poly_eval(dydx, x)) < 1e-4
# optimize__test__()

colors = 'bg'
ged_color = 0    

def poly_fit(x, y, deg):
    V = numpy.array([[i**j for j in range(deg + 1)] for i in x])
    poly_out = numpy.dot(numpy.linalg.inv(numpy.dot(V.T, V)), numpy.dot(V.T, y))
    return poly_out

def rsquared(y, fit):
    '''http://en.wikipedia.org/wiki/Coefficient_of_determination'''
    SStot = sum((y - numpy.mean(y) ) ** 2)
    SSreg = sum((y - fit) ** 2)
    return 1. - SSreg/SStot

def rsquared__test__():
    #n = 5
    #x = numpy.arange(n)
    #y = x + numpy.random.random(n)
    #fit = poly_eval(poly_fit(x, y, 1), x)
    y   = numpy.array([ 0.28188045,  1.79540073,  2.75586935,  3.8127637,   4.62600413])
    fit = numpy.array([ 0.51326161,  1.58382264,  2.65438367,  3.7249447,   4.79550573])
    # checked here: https://www.easycalculation.com/statistics/r-squared.php
    assert abs(rsquared(y, fit) - 0.987502646644) < 1e-4
rsquared__test__()

def inv_fit(x, y):
    '''
    y = a/x
    '''
    yinv = 1./y
    V = yinv
    a = numpy.dot(V, x) / numpy.dot(V, V)
    return a

def inv_fit__test__():
    x = numpy.arange(.1, 2, .01)
    y = 1/x
    assert abs(1- inv_fit(x, y)) < 1e-8
    y = 2/x
    assert abs(2 - inv_fit(x, y)) < 1e-8, '%s != 2' % inv_fit(x, y)
    y = .2/x
    assert abs(.2 - inv_fit(x, y)) < 1e-8, '%s != 2' % inv_fit(x, y)
inv_fit__test__()

def exp_fit(x, y):
    '''
    return a, b such that y ~= a exp(b * x)
    '''
    lny = numpy.log(y)
    n = len(y)
    A = numpy.ones((n, 2))
    A[:, 1] = x
    lna, b = numpy.dot(numpy.linalg.inv(numpy.dot(A.T, A)), numpy.dot(A.T, lny))
    a = numpy.exp(lna)
    return a, b
def exp_fit__test__():
    a = 1
    b = 10
    x = numpy.arange(0, 10, .1)
    y = a * numpy.exp(b * x)
    _a, _b = exp_fit(x, y)
    assert abs(a - _a) < 1e-8
    assert abs(b - _b) < 1e-8
    
def power_fit(x, y):
    '''
    y ~= a x ^ b
    '''
    out = poly_fit(numpy.log(x), numpy.log(y), 1)
    out[0] = exp(out[0])
    return out

def power_fit__test__():
    a = 2
    b = 1.2
    x = numpy.arange(1, 3)
    y = a * (x ** b)
    _a, _b = power_fit(x, y)
    assert abs(a - _a) < 1e-8
    assert abs(b - _b) < 1e-8
power_fit__test__()

def get_edited_deltas(raw_data, filtered, eps, do_plot=False, dt=defaults['dt']):
    '''
    return edited deltas from data.
    '''
    global ged_color
    # filtered = filtered[numpy.where(numpy.less(raw_data, 50))]
    peaks, troughs = find_peaks_and_troughs(filtered, eps)

    if peaks[0] < troughs[0]:
        peaks = peaks[1:]
    
    n_hill = min([len(peaks), len(troughs)])
    peaks = peaks[:n_hill]
    troughs = troughs[:n_hill]
    raw_deltas = filtered[peaks] - filtered[troughs]
    ########################################################
    ### TJS: simple heartrate computation, # beats / # minutes
    if len(peaks) > 1:
        HR = int(float(n_hill) / ((peaks[-1] - peaks[0])  * dt / 60.) + 0.5)
        # print 'n_hill', n_hill
        # print 'dur', peaks[-1], peaks[0], peaks[-1] - peaks[0]
        # print 'dt', dt

    ########################################################

    # p6 = poly_fit(x, raw_deltas, deg)
    deltas_ii = edit_deltas(raw_deltas, do_plot=do_plot)
    deltas = raw_deltas[deltas_ii]
    MAP_ii = numpy.argmax(deltas)
    MAP_peak_i = peaks[MAP_ii]
    # print 'MAP_peak_i', MAP_peak_i
    # print 'MAP6_peak_i', MAP6_peak_i
    MAP_trough_i = troughs[MAP_ii]

    MAP = raw_data[MAP_trough_i]
    MAP_delta = numpy.max(deltas)
    SBP_delta = MAP_delta * 0.55
    DBP_delta = MAP_delta * 0.85

    max_raw_delta_index = numpy.argmax(raw_deltas)
    if max_raw_delta_index == 0:
        max_raw_delta_index = 1
    SBP_ii = numpy.argmin(numpy.abs(SBP_delta - 
                                    raw_deltas[0:max_raw_delta_index]))
    DBP_ii = (numpy.argmin(numpy.abs(DBP_delta - 
                                     raw_deltas[max_raw_delta_index:])) + 
              numpy.argmax(raw_deltas))

    SBP_i = troughs[SBP_ii]
    DBP_i = troughs[DBP_ii]
    SBP = raw_data[SBP_i]
    DBP = raw_data[DBP_i]
    # print 'map est', .33 * SBP + .67 * DBP, 'MAP',  MAP  # , 'MAP6', MAP6
    if do_plot and 'deltas' in do_plot:
        inds = numpy.arange(len(raw_deltas))# - MAP_ii
        do_plot['deltas'].plot(inds, raw_deltas)
        do_plot['deltas'].plot(deltas_ii, deltas)
        do_plot['deltas'].xlabel("$\\Delta$ index")
        do_plot['deltas'].ylabel("$\\Delta$")
        do_plot['deltas'].text(SBP_ii, raw_deltas[SBP_ii], 'SBP Location')
        do_plot['deltas'].text(DBP_ii, raw_deltas[DBP_ii], 'DBP Location')
        do_plot['deltas'].plot([0, SBP_ii], [raw_deltas[SBP_ii], raw_deltas[SBP_ii]], 'r--')
        do_plot['deltas'].plot([0, DBP_ii], [raw_deltas[DBP_ii], raw_deltas[DBP_ii]], 'r--')
        # do_plot['deltas'].plot(my_peaks, poly_eval(quartic, my_peaks), 'r-')
    if do_plot and 'deflation' in do_plot:
        do_plot['deflation'].plot(raw_data[:])
        do_plot['deflation'].xlabel('count')
        do_plot['deflation'].ylabel('raw data')
    if do_plot and 'peaks' in do_plot:
        n = len(filtered) # align MAP to x = 0
        inds = numpy.arange(n) - MAP_trough_i
        do_plot['peaks'].plot(inds, filtered[:])
        for i in deltas_ii:
            p = peaks[i]
            t = troughs[i]
            do_plot['peaks'].plot([p - MAP_trough_i, t - MAP_trough_i], [filtered[p], filtered[t]], '%s-o' % colors[ged_color])
        do_plot['peaks'].plot([0, MAP_peak_i - MAP_trough_i], [filtered[MAP_trough_i], filtered[MAP_peak_i]], 'r-')
        # do_plot['peaks'].plot([MAP6_trough_i - MAP_peak_i + 40, MAP6_peak_i - MAP_peak_i + 40], [filtered[MAP6_trough_i], filtered[MAP6_peak_i]], 'm-')
        ged_color += 1
        ged_color %= len(colors)

        do_plot['peaks'].xlabel('MAP relative samples#')
        do_plot['peaks'].ylabel('BandPass filtered data [.5, 5]')
        do_plot['peaks'].ylim(-2, 2)

    if do_plot and 'deflation' in do_plot:
        do_plot['deflation'].plot([SBP_i], [SBP], 'bo')
        do_plot['deflation'].plot([DBP_i], [DBP], 'bo')
        do_plot['deflation'].plot([0, SBP_i], [SBP, SBP], 'b--')
        do_plot['deflation'].plot([0, MAP_trough_i], [MAP, MAP], 'r--')
        do_plot['deflation'].plot([0, DBP_i], [DBP, DBP], 'g--')
        do_plot['deflation'].text(SBP_i, SBP, 'SBP')
        do_plot['deflation'].text(DBP_i, DBP, 'DBP')

    # return deltas, MAP6, SBP, DBP, HR
    return deltas, MAP, SBP, DBP, HR

def find_pulse_peaks_and_troughs(data, dt,
                                 max_pulse_period=defaults['max_pulse_period'], 
                                 return_pulse_period=False):
    ''' return peaks, troughs
    both trimmed to same length with 
    peak following trough
    '''
    ### find max of all the data
    max_i = numpy.argmax(data)
    ### look backward for next trough to the left
    i = max_i

    ### find min to the left
    max_pulse_period_samples = int(max_pulse_period / dt)
    start = max_i - max_pulse_period_samples / 2
    start = max([0, start])
    end = max_i + max_pulse_period_samples / 2
    if max_i > 0:
        min_left = start + numpy.argmin(data[start:max_i])
    else:
        min_left = start
    min_right = max_i + numpy.argmin(data[max_i:end])
    pulse_period = (min_right - min_left) * dt

    fmin = defaults['min_pulse_freq']
    fmax = defaults['max_pulse_freq']
    dfreq = 1. / (len(data) * defaults['dt'])
    nfreq = int((fmax - fmin) / dfreq) + 1

    pulse_period = find_pulse_period(data, defaults['dt'], fmin, fmax, fast=True)

    # pulse_period = 1./freqs[peak]

    N = int(pulse_period / dt / 2)
    troughs = moving_argmax(-data, N)
    peaks = []
    for t1, t2 in zip(troughs[:-1], troughs[1:]):
        peaks.append(t1 + numpy.argmax(data[t1:t2]))
    # peaks.append(troughs[-1] + numpy.argmax(data[troughs[-1]:]))
    
    out = [peaks, troughs[:-1]]
    if return_pulse_period:
        out.append(pulse_period)
    return tuple(out)
    

def peak_follows_trough(peaks, troughs):
    if peaks[0] < troughs[0]:
        peaks = peaks[1:]
    if troughs[-1] < peaks[-1]:
        troughs = troughs[:-1]
    if len(peaks) > len(troughs):
        keep = peaks[:len(troughs)] > troughs
        if all(keep):
            peaks = peaks[:-1]
        else:
            peaks = peaks[keep]
    if len(peaks) < len(troughs):
        keep = peaks[:peaks] > troughs
        if all(keep):
            troughs = troughs[:-1]
        else:
            troughs = troughs[keep]
    return peaks, troughs

def find_pulse_period(bp_data, dt, fmin, fmax, fast=False):
    '''
    compute the partial descrete power spectral density for the time series 
    band pass data from fmin to fmax on dfreq steps up to but not including fmax
    return freqs, psd
    '''
    N = len(bp_data)
    if fast:
        F = abs(numpy.fft.rfft(bp_data)) ** 2
        f = numpy.fft.rfftfreq(N, dt)[numpy.argmax(F)]
        out = 1/f
    else:
        dfreq = 1. / (N * dt)

        freq = fmin
        max_pwr = -1
        max_freq = -1
        psds = []
        pps = []
        while freq < fmax:
            freq += dfreq
            pp = 1/freq
            real = 0
            imag = 0
            for j in range(N):
                # exp(2.j * pi * freq * j * dt)
                real += cos(2 * pi * freq * j * dt) * bp_data[j]
                imag += sin(2 * pi * freq * j * dt) * bp_data[j]
            psd = (real ** 2 + imag ** 2) / N
            psds.append(psd)
            pps.append(pp)
            if psd > max_pwr:
                max_pwr = psd
                max_freq = freq
        out = 1 / max_freq
    # pylab.figure(444); pylab.plot(pps, psds); pylab.show()
    return out

def find_pulse_peaks_and_troughs__test__():
    dt = .005
    t = numpy.arange(0, 15, dt)
    pulse_period = 1.1 # seconds per beats
    pulse_freq = 1. / pulse_period # beats per second
    data = numpy.sin(2 * pi * t * pulse_freq) + 6 * numpy.random.random(len(t)) - .5
    peaks, troughs = find_pulse_peaks_and_troughs(data, dt)

    N = int(pulse_period / dt / 2)
    assert peaks[0] > troughs[0]
    for p in peaks[:-1]:
        imin = max([0, p - N])
        imax = min([p + N, len(data)])
        test_data = data[imin:imax]
        assert data[p] == max(test_data)
    for t in troughs[1:]:
        imin = max([0, t - N])
        imax = min([t + N, len(data)])
        test_data = data[imin:imax]
        assert data[t] == min(test_data)

# for i in range(10):
#     find_pulse_peaks_and_troughs__test__()
# here    
def find_peaks_and_troughs(data, eps, edit=False):
    '''
    find induces of local maxima and minima in data
    '''
    
    maxtab, mintab = peakdetect.peakdet(data, eps)
    peaks = numpy.array([l[0] for l in maxtab])
    troughs = numpy.array([l[0] for l in mintab])
    return peaks, troughs

def find_peaks3(data, eps, do_plot=False):
    peaks, troughs = find_peaks_and_troughs(data, eps)
    return peaks

def find_peaks2(data, eps, *args, **kw):
    left = data[1:] - data[:-1]

    out = left[1:] * left[:-1] * numpy.greater(left, 0)[:-1]
    out = numpy.sign(out)
    out = numpy.where(numpy.less(out, 0))[0]
    # pylab.plot(data[out])
    out = out + 1
    if out[0] == len(data) - 1:
        out = out[1:]
    if out[-1] == len(data) - 1:
        out = out[:-1]
    return out

def find_peaks(data, eps, n_max=30, do_plot=False):
    ''' 
    return induces of local maxima in data
    '''
    data = numpy.array(data)
    mx = max(data)
    mn = min(data)
    # data *= numpy.greater(data, 0)

    if abs(mx - mn) < eps:
        out = []
    else:
        i_max = numpy.argmax(data)
        i = i_max
        while i > 0 and data[i - 1] < data[i]:
            i -= 1
        lo = i
        i = i_max
        while i < len(data) - 1 and data[i + 1] < data[i]:
            i += 1
        hi = i
        if 'peaks' in do_plot:
            do_plot['peaks'].plot(range(lo, hi), data[lo:hi], 'r-')
            do_plot['peaks'].plot([lo, hi], [data[lo], data[hi]], 'ro')

        data = numpy.array(data, copy=True)
        data[lo:hi+1] = min(data)
        if i_max != len(data) - 1:
            out = [i_max]
        else:
            out = []
        if len(out) < n_max:
            out.extend(find_peaks(data, eps, n_max=n_max - 1, do_plot=do_plot))
        else:
            warnings.warn('n_max::Found maximum number of peaks')
    return out

def bandpass(data, dt, lo, hi):
    '''
    Filter the data so that energy outside of pass band is attenuated
    data -- real data sampled at dt
    dt -- time between data samples
    lo -- low freq cuttoff
    hi -- hi freq cuttoff
    '''
    BW = 1/(2 * dt)
    wp = (lo / BW, hi/BW)
    ws = (lo * .4/BW, hi * 1.4 / BW)
    gpass = 1
    gstop = 20
    N, Wn = signal.buttord(wp, ws, gpass, gstop)
    # b, a = signal.butter(N, Wn, btype='bandpass')
    b, a = signal.butter(5, Wn, btype='bandpass')
    return signal.lfilter(b, a, data)

def get_bandpass_taps(lo=.5, hi=5, dt=defaults['dt'], n=defaults['n_tap']):
    BW = 1/(2 * dt)
    w1 = signal.firwin(n, hi / BW, window='blackmanharris') 
    w2 = signal.firwin(n, lo / BW, window='blackmanharris')
    w = w1 - w2
    return w 

def get_lowpass_taps(hi=5, dt=defaults['dt'], n=defaults['n_tap']):
    BW = 1/(2 * dt)
    return signal.firwin(n, hi / BW, window='blackmanharris') 

def filter(data, taps, initial=None):
    '''
    Apply FIR filter to data.
    data -- input data to be filtered
    tabs -- filter coefficients
    '''
    if False:
        # prime the output data
        init = numpy.zeros(len(taps) - 1)
        for i in range(1, len(taps)):
            init[i - 1] = numpy.dot(taps[-i:], data[:i])
        initial = init
    out = signal.lfilter(taps, 1, data)
    if False:
########TJS: correct for filter delay
        out2 = numpy.zeros(len(out) - len(taps)//2)
        out2[:] = out[len(taps)//2:]
        out = out2
    return out
def bandpass_filter__test__():
    numpy.random.seed(0)
    N = 2000
    dt = DT
    freqs = numpy.fft.fftfreq(N, dt)[:N//2 + 1]
    t = numpy.arange(N) * dt
    mid = exp(2.j * pi * (2.5 * t)) / sqrt(N)
    out_of_band = exp(2.j * pi * (0 * t)) / sqrt(N)
                   
    dat = []
    t = numpy.arange(N) * dt
    freqs = numpy.arange(0, 10, .1)
ls_color = 0
def locate_steps(inflation_data, do_plot=False, dV=10):
    '''
Inputs:
    inflation_data
    dV -- constant volume of air added per step
Outputs:
    steps, M x 2 float array of mean cuff presure MCP, and cuff 
    complaince CC (dV/dP) data.
    (M = length of returned array)
Dependencies:
    None
Calling modules:
    self calibrate
Discussion:
Data processing techniques will be used to automatically determine the "steps" of the cuff inflation phase.  Steps are defined by longer periods of relatively constant pressure, followed by brief periods of rapid pressure rise
'''
    global ls_color
    if do_plot == False:
        do_plot = {}
    ## low pass filter
    ifiltered = (filter(inflation_data - MIN_PRESSURE, get_lowpass_taps(1e-8))
                 + MIN_PRESSURE)

    # numeric derivative
    dfiltered = ifiltered[1:] - ifiltered[:-1]
    peaks = list(find_peaks3(dfiltered, DT))
    peaks.insert(0, 0)
    peaks.append(len(dfiltered) - 1)
    peaks.sort()
    peaks = numpy.array(peaks)
        
    if False: # find plateaus using peaks of derivative
        plateaus = (peaks[1:] + peaks[:-1]) // 2
        plateaus = plateaus[1:]
    else: # find plateaus using troughs of derivative function
        troughs = list(find_peaks3(-dfiltered, DT))
        troughs.sort()
        if troughs[0] == 0:
            troughs = troughs[1:]
        # print troughs

        if troughs[1] == len(troughs) - 1:
            troughs = troughs[:-1]
        plateaus = troughs
        
    MCP = ifiltered[plateaus]
    # MCP = ifiltered[peaks[1:]] # remove first peak
    # put x coord at midpoint, other choices 
    #     RIGHT: MCP = MCP[1:] 
    #     LEFT : MCP = MCP[:-1] 
    # MCP = (MCP[1:] + MCP[:-1]) / 2. # middle (works)
    # MCP = MCP[1:]                   # upper (bad)
    MCP = MCP[:-1]                  # lower
    

    dP = ifiltered[plateaus[1:]] - ifiltered[plateaus[:-1]]
    
    CC = dV / dP
    if 'inflation' in do_plot:
        do_plot['inflation'].plot(inflation_data, '%s-' % colors[ls_color])
        # do_plot['inflation'].plot(ifiltered)
        for hi, lo in zip(plateaus[1:], plateaus[:-1]):
            do_plot['inflation'].plot([lo, hi], 
                                      [ifiltered[lo], ifiltered[hi]], '%s--' % colors[ls_color])
        do_plot['inflation'].title('Inflation Data')
        # do_plot['inflation'].plot(peaks, ifiltered[peaks], '%so' % colors[ls_color])
        do_plot['inflation'].plot(plateaus, ifiltered[plateaus], '%so' % colors[ls_color])
        ls_color += 1
        ls_color %= len(colors)

    if 'slope_inflation' in do_plot:
        do_plot['slope_inflation'].title("Slope of the inflation data")
        do_plot['slope_inflation'].plot(dfiltered)
        do_plot['slope_inflation'].plot(peaks, dfiltered[peaks], 'bo')
        do_plot['slope_inflation'].plot(plateaus, dfiltered[plateaus], 'ro')

    if 'ccc' in do_plot:
        # TJS: The CCC curve should be repeatable if the cuff does not change.
        do_plot['ccc'].plot(MCP, CC, '%so' % colors[ls_color])
        do_plot['ccc'].title("CCC")
        do_plot['ccc'].xlabel("MCP")
        do_plot['ccc'].ylabel("CC = dV/dP")
        
    out = MCP, CC
    return out

def partition_data(data, do_plot=False, offset=200, hold_sec=0):
    '''
    Partition into three regions:
    inflation, hold, deflation.

    returns istart, istop, dstart, dstop

    inflation = data[istart:istop]
    hold = data[istop:dstart]
    deflation = data[dstart:dstop]
    
    TJS: inflation data starts at 20mm HG
    '''
    if do_plot is False:
        do_plot = {}
    # TODO: compute hold data for experimental set
    imax = numpy.argmax(data)
    #offset = 1000
    if True: #hold_sec > 0:
        # find drop in trough in derivative near hold secs
        start_i = imax + (hold_sec - 10) / DT
        if start_i < imax:
            start_i = imax
        dat = data[start_i:imax + (hold_sec + 10) / DT]
        der = (dat[1:] - dat[:-1]) / DT
        corner = numpy.argmin(der)
        # out = 0, imax + offset, start_i + corner, len(data) - 1
        start = numpy.where(numpy.greater(data, 20))[0][0] + 1
        out = start, imax + offset, start_i + corner, len(data) - 1
    else:
        out = 0, imax + offset, imax + offset + hold_sec / DT, len(data) - 1
    if 'raw' in do_plot:
        do_plot['raw'].plot(data)
        do_plot['raw'].plot(out, [data[i] for i in out], 'ro')
        
    return out

def mfreqz(b,a=1):
    '''
    #Plot frequency and phase response
    from http://mpastell.com/2010/01/18/fir-with-scipy/
    '''
    w,h = signal.freqz(b,a)
    h_dB = 20 * log10 (abs(h))
    pylab.subplot(211)
    pylab.plot(w/max(w),h_dB)
    pylab.ylim(-150, 5)
    pylab.ylabel('Magnitude (db)')
    pylab.xlabel(r'Normalized Frequency (x$\pi$rad/sample)')
    pylab.title(r'Frequency response')
    pylab.subplot(212)
    h_Phase = pylab.unwrap(arctan2(imag(h),real(h)))
    pylab.plot(w/max(w),h_Phase)
    pylab.ylabel('Phase (radians)')
    pylab.xlabel(r'Normalized Frequency (x$\pi$rad/sample)')
    pylab.title(r'Phase response')
    pylab.subplots_adjust(hspace=0.5)

def impz(b,a=1):
    '''
    #Plot step and impulse response
    from http://mpastell.com/2010/01/18/fir-with-scipy/
    '''
    l = len(b)
    impulse = pylab.repeat(0.,l); impulse[0] =1.
    x = numpy.arange(0,l)
    response = signal.lfilter(b,a,impulse)
    pylab.subplot(211)
    pylab.stem(x, response)
    pylab.ylabel('Amplitude')
    pylab.xlabel(r'n (samples)')
    pylab.title(r'Impulse response')
    pylab.subplot(212)
    step = numpy.cumsum(response)
    pylab.stem(x, step)
    pylab.ylabel('Amplitude')
    pylab.xlabel(r'n (samples)')
    pylab.title(r'Step response')
    pylab.subplots_adjust(hspace=0.5)

def find_peaks_and_troughs__test__():
    N = 1000
    t = numpy.arange(N)
    f1 = .02
    f2 = .002
    data1 = sin(2 * pi * f1 * t) - .5 * cos(2 * pi * f2 * t)
    # data1 *= -1
    peaks, troughs = find_peaks_and_troughs(data1, .1)
    assert len(peaks) == 20, '%s != 20' % len(peaks)
    assert len(troughs) == 20, '%s != 20' % len(troughs)

    f1 = .04
    f2 = .041
    data1 = sin(2 * pi * f1 * t) - .5 * cos(2 * pi * f2 * t)
    # data1 *= -1
    peaks, troughs = find_peaks_and_troughs(data1, 2)
    if False:
        pylab.plot(data1)
        pylab.plot(peaks, data1[peaks], 'ro')
        pylab.plot(troughs, data1[troughs], 'go')
        pylab.show()
        here
# find_peaks_and_troughs__test__()
def find_peaks__test__():
    N = 1000
    t = numpy.arange(N)
    f1 = .02
    f2 = .002
    data1 = sin(2 * pi * f1 * t) - .5 * cos(2 * pi * f2 * t)
    # data1 *= -1
    uut = find_peaks3

    peaks = uut(data1, .1, do_plot=False)
        
    assert len(peaks) == 20, '%s != 20' % len(peaks)
    for peak in peaks:
        if peak > 0:
            assert data1[peak] >= data1[peak - 1]
        if peak < len(data1) - 1:
            assert data1[peak] >= data1[peak + 1]

    data1 = data1 - 20
    peaks = uut(data1, .1, do_plot=False)
    assert len(peaks) == 20
    for peak in peaks:
        if peak > 0:
            assert data1[peak] >= data1[peak - 1]
        if peak < len(data1) - 1:
            assert data1[peak] >= data1[peak + 1]

def edit_deltas(deltas, do_plot=False):
    '''
    returns induces of deltas satisfying these steps

Software steps step 4)
Edit the journal peak data using the following general 
rules
a. When starting from the highest cuff pressure and moving towards MAP, 
delete all journal data entries where dP decreases.(Note: Usually MAP 
is between 70 mmHg and 110 mmHg)
b. When starting from MAP and moving towards 0 mm Hg delete all journal
data entries where dP increases.
    '''
    # return numpy.arange(len(deltas))
    MAPi = numpy.argmax(deltas)    
    out = [0]
    for i in range(1, MAPi):
        if deltas[out[-1]] < deltas[i]:
            out.append(i)
    out.append(MAPi)
    for i in range(MAPi, len(deltas)):
        if deltas[out[-1]] > deltas[i]:
            out.append(i)
    return out

def edit_deltas__test__():
    deltas = numpy.array([1, 2, 3, 4, 5, 5, 5, 6, 7, 6, 5, 6,7,8,9,9, 10, 
                          9, 8, 7, 6, 5, 6,5, 4, 3, 4, 3,2, 1])
    keepers = edit_deltas(deltas, do_plot=False)
    kd = deltas[keepers]
    ddeltas = kd[1:] - kd[:-1]
    dddeltas = ddeltas[1:] - ddeltas[:-1]
    assert numpy.sum(numpy.less(dddeltas, 0)) == 1

def grabCol(filename, skiprows=1, col=0):
    if filename.lower().endswith('.txt'):
        file = open(filename)
        for i in range(skiprows):
            file.readline()
        dat = [l.split('\t')[col] for l in file.xreadlines()]
        if 'normal' in filename:
            hyper = filename.replace('normal', 'hyper')
            if os.path.exists(hyper):
                file = open(hyper)
                for i in range(skiprows):
                    file.readline()
                hdat = [l.split('\t')[col] for l in file.xreadlines()]
                dat.extend(hdat)
        dat = numpy.array(map(float, dat[:-2]))
    elif filename.lower().endswith('.acq'):
        dat = bioread.read_file(filename).channels[0].data
    else:
        raise Exception("Unknown file type %s" % filename)
    return dat        

def __grabCol__test__():
    c = grabCol('../input/AS_normal.TXT')
    assert len(c.shape) == 1
    c + c # assert numeric type

def decimate(data, fs_ratio=200/20, n_tap=defaults['n_tap']):
    fs_ratio = int(fs_ratio)
    taps = get_lowpass_taps(1./fs_ratio, dt=1., n=n_tap)
    return filter(data, taps)[::fs_ratio]

def __decimate__test__():
    data = numpy.random.normal(0, 1, 10000)
    data = decimate(data)
    assert len(data) == 950, '%s != 950' % len(data)
    
class StreamingFir:
    def __init__(self, taps, initial_val=0., decimate=10):
        self.z = numpy.ones(len(taps) - 1) * initial_val
        self.taps = taps
        self.deci = decimate
        self.staging = numpy.zeros(self.deci)
        self.out = []
        self.count = 0
        
    def update(self, x):
        self.staging[self.count % self.deci] = x
        self.count += 1
        if (self.count % self.deci) == 0:
            filtered, self.z = signal.lfilter(self.taps, 1., self.staging, zi=self.z)
            self.out.append(filtered[-1])

    def __call__(self, x):
        return self.update(x)
    def getLast(self):
        if self.count > self.deci:
            out = self.out[-1]
        else:
            out = self.z[-1]
        return out
    last = property(getLast)

LP_TAPS = get_lowpass_taps(defaults['high_cuttoff_hz'], 
                           defaults['dt'],
                           defaults['n_tap'])
LLP_TAPS = get_lowpass_taps(defaults['low_cuttoff_hz'], 
                            defaults['dt'],
                            defaults['n_tap'])
DELAY_TAPS = numpy.zeros(defaults['n_tap'])
DELAY_TAPS[defaults['n_tap'] // 2] = 1

# get_bandpass_taps()
if defaults['run_unittests']:
  import pretest
  pretest.pretest('util')
