"""
debug_BP.py -- BP debug GUI: Start button -> run measurement -> show diagnostic plots.

Usage:
    python debug_BP.py           # dummy mode (no hardware)
    python debug_BP.py --real    # use hardware via uControl

Key design:
  - Record from start of inflation so we have the full picture for panel 0.
  - find_release_idx() locates where deflation actually starts in raw data
    (the big drop after the hold plateau).
  - Filters (LP, LLP) are applied ONLY to the descent portion, baseline-
    corrected so the filter sees a signal starting near zero:
        descent = raw[release_idx:] - raw[release_idx]
        lp  = filter(descent) + raw[release_idx]
    This prevents the high inflation pressure from dragging the LLP baseline
    and corrupting the bandpass during the medically relevant descent.
"""

import sys
import os
import threading
import numpy

import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import util
from constants import defaults

INFLATE_MMHG = 220
DEFLATE_MMHG = 30
HOLD_SEC     = 2.0


# ---------------------------------------------------------------------------
# Vectorised poly_eval (fixes the scalar-only bug in util.poly_eval)
# ---------------------------------------------------------------------------
def poly_eval_vec(poly, x):
    x = numpy.asarray(x, dtype=float)
    return sum(poly[i] * x**i for i in range(len(poly)))


# ---------------------------------------------------------------------------
# Dummy data — inflation ramp + 2s hold + deflation descent
# Returns (raw, release_idx)
# ---------------------------------------------------------------------------
def make_dummy_data():
    dt  = defaults['dt']
    rng = numpy.random.default_rng(42)

    # inflation ramp 0->220 over 3s
    n_ramp = int(3.0 / dt)
    ramp   = numpy.linspace(0, 220, n_ramp)

    # 2s hold at 220
    n_hold = int(HOLD_SEC / dt)
    hold   = numpy.full(n_hold, 220.0)

    # deflation descent 220->30 over 37s with oscillometric pulses
    n_desc  = int(37.0 / dt)
    t_desc  = numpy.arange(n_desc) * dt
    cuff    = 220.0 - 190.0 * (t_desc / t_desc[-1])
    amp_env = numpy.exp(-((cuff - 95) ** 2) / (2 * 25 ** 2)) * 8.0
    pulses  = amp_env * numpy.sin(2 * numpy.pi * 1.1 * t_desc)
    descent = cuff + pulses

    noise       = rng.normal(0, 0.15, n_ramp + n_hold + n_desc)
    raw         = numpy.concatenate([ramp, hold, descent]) + noise
    release_idx = n_ramp + n_hold   # first sample of deflation descent

    return raw, release_idx


# ---------------------------------------------------------------------------
# Find the release point in raw hardware data.
# The hold plateau ends with a rapid pressure drop when the valve opens.
# We find the peak of raw then look for a sustained negative slope.
# ---------------------------------------------------------------------------
def find_release_idx(raw, dt, slope_thresh=-5.0, sustain_sec=0.2):
    """
    Returns the index in raw where deflation begins.
    slope_thresh : mmHg/s — slope must be more negative than this
    sustain_sec  : how long the slope must stay negative to confirm release
    """
    peak_idx = int(numpy.argmax(raw))
    win      = max(1, int(sustain_sec / dt))
    # smooth derivative (10-sample window)
    smooth   = numpy.convolve(raw, numpy.ones(10) / 10, mode='same')
    slope    = numpy.diff(smooth) / dt
    return 0
    for i in range(peak_idx, len(slope) - win):
        if numpy.all(slope[i:i + win] < slope_thresh):
            return i

    return peak_idx   # fallback


# ---------------------------------------------------------------------------
# Core analysis — filters only the descent, baseline corrected
# ---------------------------------------------------------------------------
def analyse(raw, dt, release_idx):
    # --- descent-only, baseline corrected ---
    baseline = raw[release_idx]
    descent  = raw[release_idx:] - baseline   # starts near 0

    lp_full  = util.filter(descent, util.LP_TAPS)  + baseline
    llp_full = util.filter(descent, util.LLP_TAPS) + baseline

    # Skip n_tap samples so FIR filters have settled before peak detection
    n_tap = defaults["n_tap"]
    skip = n_tap # * 3 // 2
    lp  = lp_full[skip:]
    llp = llp_full[skip:]
    bpf = lp - llp

    troughs, peaks, deltas = util.get_troughs_peaks_deltas(bpf)

    # Reject pulses longer than 2x the median pulse period
    periods     = numpy.diff(troughs) * dt
    mean_period = numpy.median(periods)
    max_period  = 2.0 * mean_period
    keep = numpy.array([(t2 - t1) * dt < max_period
                        for t1, t2 in zip(troughs[:-1], troughs[1:])],
                       dtype=bool)
    keep    = numpy.append(keep, True)
    troughs = troughs[keep]
    peaks   = peaks[keep]
    deltas  = deltas[keep]

    # n_peak logic (mirrors util.blood_pressure)
    candidate_deltas = [d for idx, d in zip(peaks, deltas) if llp[idx] > 60]
    n_peak = numpy.argmax(candidate_deltas) * 2 + 1
    if n_peak >= len(peaks):
        n_peak = len(peaks)
    if n_peak < 15:
        n_peak = min(15, len(peaks))
    n_peak = min(n_peak, len(peaks))

    p6 = util.poly_fit(troughs[:n_peak] * dt, deltas[:n_peak], 6)

    t_fit_start = troughs[0] * dt
    t_fit_end   = troughs[n_peak - 1] * dt
    t_dense     = numpy.linspace(t_fit_start, t_fit_end, 2000)
    y_poly      = poly_eval_vec(p6, t_dense)

    # MAP
    t_search = numpy.arange(peaks[0] * dt, peaks[n_peak - 1] * dt, 0.05)
    y_search = poly_eval_vec(p6, t_search)
    map_time = t_search[numpy.argmax(y_search)]
    map_idx  = int(map_time / dt)
    MAP6     = llp[map_idx]
    peak_fit = float(poly_eval_vec(p6, map_time))

    sbp_target = 0.55 * peak_fit
    dbp_target = 0.85 * peak_fit

    # SBP (walk backward from MAP)
    t_sbp  = numpy.arange(map_time, t_fit_start, -0.01)
    pt_sbp = poly_eval_vec(p6, t_sbp) - sbp_target
    below  = numpy.where(pt_sbp < 0)[0]
    if len(below):
        sbp_time = t_sbp[below[0]]
        sbp_val  = llp[int(sbp_time / dt)]
    else:
        sbp_time = sbp_val = None

    # DBP (walk forward from MAP)
    t_dbp  = numpy.arange(map_time, t_fit_end, 0.01)
    pt_dbp = poly_eval_vec(p6, t_dbp) - dbp_target
    below  = numpy.where(pt_dbp < 0)[0]
    if len(below):
        dbp_time = t_dbp[below[0]]
        dbp_val  = llp[int(dbp_time / dt)]
    else:
        dbp_time = dbp_val = None

    mad_failed = util.mad_thresh_test(
        numpy.diff(deltas), defaults['mad_thresh'], defaults['mad_n_bad_thresh'])

    return dict(
        dt=dt, raw=raw, release_idx=release_idx, baseline=baseline, n_tap=n_tap,
        lp_full=lp_full, llp_full=llp_full,
        lp=lp, llp=llp, bpf=bpf,
        peaks=peaks, troughs=troughs, deltas=deltas,
        n_peak=n_peak,
        p6=p6, t_dense=t_dense, y_poly=y_poly,
        map_time=map_time, MAP6=MAP6, peak_fit=peak_fit,
        sbp_target=sbp_target, dbp_target=dbp_target,
        sbp_time=sbp_time, sbp_val=sbp_val,
        dbp_time=dbp_time, dbp_val=dbp_val,
        mad_failed=mad_failed,
    )


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
class DebugBPApp(tk.Tk):
    def __init__(self, use_hardware=False):
        super().__init__()
        self.use_hardware = use_hardware
        self.title('BP Debug')
        self.geometry('1100x920')
        self._uc     = None
        self._thread = None
        self._build_ui()
        if use_hardware:
            self._init_hardware()
        else:
            self._set_status('Dummy mode — press Start to run a simulated measurement')

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        top = tk.Frame(self, pady=8)
        top.pack(side=tk.TOP, fill=tk.X, padx=12)

        self.start_btn = tk.Button(
            top, text='Start',
            font=('Helvetica', 16, 'bold'),
            bg='#2d7dd2', fg='white',
            activebackground='#1a5fa8', activeforeground='white',
            padx=18, pady=8,
            command=self._on_start,
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 24))

        result_frame = tk.Frame(top)
        result_frame.pack(side=tk.LEFT)
        self.sbp_var = tk.StringVar(value='SYS: ---')
        self.dbp_var = tk.StringVar(value='DIA: ---')
        tk.Label(result_frame, textvariable=self.sbp_var,
                 font=('Helvetica', 26, 'bold'), fg='#cc2222').pack(side=tk.LEFT, padx=12)
        tk.Label(result_frame, textvariable=self.dbp_var,
                 font=('Helvetica', 26, 'bold'), fg='#2255bb').pack(side=tk.LEFT, padx=12)

        status_frame = tk.Frame(self)
        status_frame.pack(fill=tk.X, padx=12)
        self.status_var = tk.StringVar(value='Initialising...')
        tk.Label(status_frame, textvariable=self.status_var,
                 font=('Helvetica', 10), anchor='w').pack(side=tk.LEFT, fill=tk.X)

        self.progress = ttk.Progressbar(self, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=12, pady=(2, 4))

        self.fig = Figure(figsize=(10.5, 8.2))
        self.ax0 = self.fig.add_subplot(411)   # full raw + release marker
        self.ax1 = self.fig.add_subplot(412)   # bandpass + peaks/troughs
        self.ax2 = self.fig.add_subplot(413)   # p6 poly
        self.ax3 = self.fig.add_subplot(414)   # cuff pressure read-off
        self.fig.tight_layout(pad=2.0)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

    # --------------------------------------------------------- hardware init
    def _init_hardware(self):
        self._set_status('Connecting to hardware...')
        self.update()
        try:
            from uControl import uControl
            self._uc = uControl(dummy=False)
            self._set_status('Connected. Press Start to measure.')
        except Exception as exc:
            self._set_status('Hardware error: %s' % exc)
            messagebox.showerror('Hardware Error', str(exc))

    # --------------------------------------------------------- button handler
    def _on_start(self):
        if self._thread and self._thread.is_alive():
            return
        self.start_btn.config(state=tk.DISABLED)
        self.sbp_var.set('SYS: ---')
        self.dbp_var.set('DIA: ---')
        self.progress.start(12)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    # --------------------------------------------------------- worker thread
    def _run(self):
        try:
            if self.use_hardware:
                raw, release_idx, dt = self._collect_from_hardware()
            else:
                self._set_status('Generating dummy data...')
                raw, release_idx = make_dummy_data()
                dt = defaults['dt']

            self._set_status('Analysing...')
            import drive
            drive.send_cmd(interval=1, pump_rate=0, valve=drive.getValveByte(False, False))

            result = analyse(raw, dt, release_idx)

            sbp_str = ('SYS: %d' % result['sbp_val']) if result['sbp_val'] is not None else 'SYS: ---'
            dbp_str = ('DIA: %d' % result['dbp_val']) if result['dbp_val'] is not None else 'DIA: ---'
            suffix  = '  [artifact]' if result['mad_failed'] else ''
            if result['sbp_val'] is not None and result['dbp_val'] is not None:
                status = 'SYS %d / DIA %d mmHg%s' % (result['sbp_val'], result['dbp_val'], suffix)
            else:
                status = 'Done%s — check plots for missing crossings' % suffix

            self.after(0, lambda s=sbp_str: self.sbp_var.set(s))
            self.after(0, lambda d=dbp_str: self.dbp_var.set(d))
            self._set_status(status)
            self.after(0, lambda r=result: self._update_plots(r))

        except Exception as exc:
            msg = str(exc)
            self._set_status('Error: %s' % msg)
            self.after(0, lambda m=msg: messagebox.showerror('Error', m))
        finally:
            self.after(0, self._done)

    def _collect_from_hardware(self):
        uc = self._uc
        if uc is None:
            raise RuntimeError('No hardware connection')

        dt = uc.dt   # 0.004 from uControl firmware

        # Reset serial buffer between runs — keep interval=1 so mpid_cb
        # keeps firing and cuff_pressure stays current during inflate/deflate.
        import drive
        drive.last_ser_data = b''
        drive.s.flushInput()
        # ensure pump is off, valve closed, sampling stream running
        drive.send_cmd(interval=1, pump_rate=0, valve=drive.getValveByte(False, False))
        uc.delay(0.5)   # let a few packets through to confirm clean state

        # reset uControl state flags (don't re-subscribe — callbacks already registered)
        uc.min_pressure = -1
        uc.max_pressure = 1e6
        uc.bleeding     = False
        uc.hirate       = []
        uc.recording    = False

        self._set_status('Inflating cuff to %d mmHg...' % INFLATE_MMHG)
        uc.maintain(0, INFLATE_MMHG, 0)

        # start recording before the hold so we have the full picture
        uc.hirate = []
        uc.record(True)

        # 2s hold at max pressure
        self._set_status('Holding at %d mmHg for %.0fs...' % (INFLATE_MMHG, HOLD_SEC))
        uc.delay(HOLD_SEC)

        # note how many samples were collected during hold — release starts here
        release_idx = len(uc.hirate)
        release_idx = 0

        self._set_status('Deflating — recording pulses...')
        uc.deflate(DEFLATE_MMHG)

        data = uc.hirate[:]
        uc.record(False)

        # release cuff fully
        self._set_status('Releasing cuff...')
        from drive import send_cmd, getValveByte
        send_cmd(pump_rate=False, valve=getValveByte(valve0=True))
        uc.delay(2)
        send_cmd(pump_rate=False, valve=getValveByte(valve0=False), interval=0)

        if len(data) < defaults['n_tap'] + 100:
            raise ValueError('Too few samples (%d)' % len(data))

        raw = numpy.array(data)[:, 1]

        # if release_idx heuristic seems off, fall back to slope detection
        if release_idx >= len(raw) - 10:
            release_idx = find_release_idx(raw, dt)

        return raw, release_idx, dt

    # --------------------------------------------------------- plotting
    def _update_plots(self, r):
        dt          = r['dt']
        raw         = r['raw']
        release_idx = r['release_idx']
        baseline    = r['baseline']
        lp          = r['lp']
        llp         = r['llp']
        bpf         = r['bpf']
        peaks       = r['peaks']
        troughs     = r['troughs']
        n_peak      = r['n_peak']
        t_dense     = r['t_dense']
        y_poly      = r['y_poly']

        n_full    = len(raw)
        lp_full   = r['lp_full']
        llp_full  = r['llp_full']
        n_tap     = r['n_tap']
        t_full    = numpy.arange(n_full) * dt
        release_t = release_idx * dt

        # descent time axes — relative to release
        t_desc = numpy.arange(len(lp)) * dt
        t_llp  = numpy.arange(len(llp)) * dt
        t_sig  = numpy.arange(len(bpf)) * dt

        # --- Panel 0: full raw + descent filters, showing release and n_tap skip ---
        t_desc_full = numpy.arange(len(lp_full)) * dt
        skip_t      = n_tap * dt   # time into descent where analysis starts

        self.ax0.cla()
        self.ax0.plot(t_full, raw, color='lightgray', lw=0.7, label='raw')
        self.ax0.plot(release_t + t_desc_full, lp_full,  color='steelblue',  lw=1.2, label='LP (descent only)')
        self.ax0.plot(release_t + t_desc_full, llp_full, color='darkorange', lw=1.5, label='LLP (descent only)')
        self.ax0.axvline(release_t, color='red', lw=1.5, ls='--',
                         label='release @ %.2fs  (%.0f mmHg)' % (release_t, baseline))
        self.ax0.axvline(release_t + skip_t, color='green', lw=1.5, ls='--',
                         label='n_tap skip ends @ %.2fs' % (release_t + skip_t))
        self.ax0.set_ylabel('Pressure (mmHg)')
        self.ax0.set_title('Full raw + descent filters — red=release, green=analysis start (n_tap settled)', fontsize=9)
        self.ax0.legend(fontsize=7, loc='upper right')

        # --- Panel 1: bandpass (descent) + peaks/troughs ---
        self.ax1.cla()
        self.ax1.plot(t_sig, bpf, color='seagreen', lw=0.8, label='Bandpass')
        self.ax1.plot(peaks * dt,   bpf[peaks],   'r^', ms=4, label='peaks')
        self.ax1.plot(troughs * dt, bpf[troughs], 'bv', ms=4, label='troughs')
        self.ax1.axvspan(troughs[0] * dt, troughs[n_peak - 1] * dt,
                         alpha=0.10, color='gold', label='fit window (n=%d)' % n_peak)
        self.ax1.axhline(0, color='gray', lw=0.5, ls='--')
        self.ax1.set_ylabel('Bandpass (mmHg)')
        self.ax1.set_title('Bandpass — peaks & troughs (t=0 is release)', fontsize=9)
        self.ax1.legend(fontsize=7, loc='upper right')

        # --- Panel 2: p6 poly + targets ---
        self.ax2.cla()
        self.ax2.plot(t_dense, y_poly, color='purple', lw=2.0, label='p6 poly')
        self.ax2.scatter(troughs[:n_peak] * dt, r['deltas'][:n_peak],
                         color='black', zorder=5, s=18, label='fit pts (delta)')
        self.ax2.axhline(r['sbp_target'], color='tomato',     lw=1.5, ls='--',
                         label='55%% SBP target = %.2f' % r['sbp_target'])
        self.ax2.axhline(r['dbp_target'], color='dodgerblue', lw=1.5, ls='--',
                         label='85%% DBP target = %.2f' % r['dbp_target'])
        self.ax2.axhline(r['peak_fit'],   color='purple',     lw=1.0, ls=':',
                         label='MAP peak = %.2f' % r['peak_fit'])
        self.ax2.axvline(r['map_time'], color='purple', lw=1.0, ls=':', alpha=0.7)
        self.ax2.plot(r['map_time'], r['peak_fit'], 'P', color='purple', ms=9,
                      zorder=6, label='MAP @ %.2fs' % r['map_time'])

        if r['sbp_time'] is not None:
            self.ax2.axvline(r['sbp_time'], color='tomato', lw=1.2, ls=':', alpha=0.8)
            self.ax2.plot(r['sbp_time'], r['sbp_target'], 'o', color='tomato', ms=8,
                          zorder=6, label='SBP @ %.2fs -> %d mmHg' % (r['sbp_time'], r['sbp_val']))
        else:
            self.ax2.text(0.5, 0.5, 'SBP NOT FOUND', transform=self.ax2.transAxes,
                          ha='center', color='red', fontsize=12, fontweight='bold')

        if r['dbp_time'] is not None:
            self.ax2.axvline(r['dbp_time'], color='dodgerblue', lw=1.2, ls=':', alpha=0.8)
            self.ax2.plot(r['dbp_time'], r['dbp_target'], 'o', color='dodgerblue', ms=8,
                          zorder=6, label='DBP @ %.2fs -> %d mmHg' % (r['dbp_time'], r['dbp_val']))
        else:
            self.ax2.text(0.5, 0.4, 'DBP NOT FOUND', transform=self.ax2.transAxes,
                          ha='center', color='blue', fontsize=12, fontweight='bold')

        self.ax2.set_ylabel('Peak-to-trough\n delta (mmHg)')
        self.ax2.set_title('p6 polynomial fit — 55%%/85%% SBP/DBP targets', fontsize=9)
        self.ax2.legend(fontsize=7, loc='upper right')

        # --- Panel 3: cuff pressure read-off ---
        self.ax3.cla()
        self.ax3.plot(t_llp, llp, color='darkorange', lw=1.5, label='Cuff LLP (descent)')
        self.ax3.axvline(r['map_time'], color='purple', lw=1.0, ls=':', alpha=0.7)
        self.ax3.axhline(r['MAP6'],    color='purple', lw=1.0, ls=':', alpha=0.7)
        self.ax3.plot(r['map_time'], r['MAP6'], 'P', color='purple', ms=9,
                      zorder=6, label='MAP = %d mmHg' % r['MAP6'])

        if r['sbp_time'] is not None:
            self.ax3.axvline(r['sbp_time'], color='tomato', lw=1.2, ls=':', alpha=0.8)
            self.ax3.axhline(r['sbp_val'], color='tomato', lw=1.0, ls=':', alpha=0.6)
            self.ax3.plot(r['sbp_time'], r['sbp_val'], 'o', color='tomato', ms=8,
                          zorder=6, label='SBP = %d mmHg' % r['sbp_val'])

        if r['dbp_time'] is not None:
            self.ax3.axvline(r['dbp_time'], color='dodgerblue', lw=1.2, ls=':', alpha=0.8)
            self.ax3.axhline(r['dbp_val'], color='dodgerblue', lw=1.0, ls=':', alpha=0.6)
            self.ax3.plot(r['dbp_time'], r['dbp_val'], 'o', color='dodgerblue', ms=8,
                          zorder=6, label='DBP = %d mmHg' % r['dbp_val'])

        self.ax3.set_xlabel('Time from release (s)')
        self.ax3.set_ylabel('Cuff pressure\n(mmHg)')
        self.ax3.set_title('Cuff pressure — MAP / SBP / DBP read-off', fontsize=9)
        self.ax3.legend(fontsize=7, loc='upper right')

        self.fig.tight_layout(pad=2.0)
        self.canvas.draw()

    # --------------------------------------------------------- helpers
    def _done(self):
        self.progress.stop()
        self.start_btn.config(state=tk.NORMAL)

    def _set_status(self, msg):
        self.after(0, lambda m=msg: self.status_var.set(m))


# ---------------------------------------------------------------------------
if __name__ == '__main__':
    use_hardware = not '--sym' in sys.argv
    app = DebugBPApp(use_hardware=use_hardware)
    app.mainloop()
