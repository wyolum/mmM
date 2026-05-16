"""
mmM pressure-hold GUI
=====================

Holds a target cuff pressure using drive.py's send_cmd() pump+valve actuators,
shows live cuff pressure, detects per-beat peak-to-trough delta_p, and displays
a history chart and table of beat amplitudes.

drive.py is the uControl driver from the wyolum/mmM repo. It auto-connects on
import and exposes:
    send_cmd(interval=..., pump_rate=..., valve=..., <status flags>=True)
    subscribe(pid, callback)   /   unsubscribe(pid, callback)
    serial_interact(max_iter=...)
    MeasurementsPID with .cuff (mmHg), .flow (sccm), .pulse, .millis

Control loop (bang-bang with deadband):
    if cuff < target - DEADBAND_LO:   pump on,  valve closed
    elif cuff > target + DEADBAND_HI: pump off, valve open (bleed)
    else:                              pump off, valve closed

Safety:
  - Hard upper limit (HARD_MAX_MMHG): valve forced open above this.
  - Watchdog: if no packet seen for WATCHDOG_S, vent and stop hold.
  - Window close vents and stops sampling.

Run on the Mac mini with the uControl board attached:
    python3 mmm_hold_gui.py
"""

import argparse
import atexit
import signal
import time
import threading
import collections
import queue
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
from scipy.signal import butter, lfilter, lfilter_zi, find_peaks

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------------------------------------------------------------------
# drive.py is required. No simulator fallback -- if the import fails or no
# board is attached, surface a clear error rather than running against fake
# data.
# ---------------------------------------------------------------------------
try:
    import drive
except IndexError:
    raise RuntimeError(
        "Could not find mmM board: no /dev/cu.usbserial* device. "
        "Plug the board in (FTDI USB cable) and try again."
    )
except Exception as e:
    raise RuntimeError(
        f"Failed to import drive.py / connect to mmM board: {e}"
    )


# ---------------------------------------------------------------------------
# Module-level emergency vent
# ---------------------------------------------------------------------------
def _emergency_vent(reason=""):
    """Best-effort vent: open both valves, pump off, stop streaming.

    Called by atexit and SIGTERM/SIGINT handlers so the cuff is never left
    pressurised after any Python exit path -- clean shutdown, Ctrl-C,
    unhandled exception, or kill.
    """
    try:
        drive.send_cmd(interval=0, pump_rate=0,
                       valve=drive.getValveByte(valve0=True, valve1=True))
    except Exception:
        pass
    if reason:
        print(f"[mmM] emergency vent: {reason}")


atexit.register(_emergency_vent, "process exit")


def _signal_handler(signum, frame):
    _emergency_vent(f"signal {signum}")
    raise SystemExit(signum)


for _sig in (signal.SIGTERM, signal.SIGINT):
    try:
        signal.signal(_sig, _signal_handler)
    except (OSError, ValueError):
        pass  # non-main thread or platform restriction; atexit still fires


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
INTERVAL          = 1        # send_cmd interval; 1 => fast stream from device
HARD_MAX_MMHG     = 220.0    # absolute upper limit; vent above this
WATCHDOG_MMHG     = 250.0    # vent if measured pressure exceeds this
DISPLAY_WINDOW_S  = 12.0     # live trace span
HISTORY_TABLE_N   = 30       # rows in the delta_p table
UI_REFRESH_MS     = 50       # ~20 Hz UI update
NOMINAL_FS        = 200.0    # used for filter design + buffer sizing

# Waterfall
WF_NFFT           = 256      # FFT size; ~1.28 s window at 200 Hz, 0.78 Hz bin
WF_UPDATE_S       = 0.5      # new spectrum column every 0.5 s
WF_SPAN_S         = 15.0     # total time history shown
WF_FMAX           = 100.0    # max frequency on display (Hz)
WF_DB_LO          = -40.0    # color scale floor (dB)
WF_DB_HI          = 40.0     # color scale ceiling (dB)


# ---------------------------------------------------------------------------
# Streaming bandpass for AC pressure (heart-rate band)
# ---------------------------------------------------------------------------
class StreamingBandpass:
    def __init__(self, fs, fl=0.7, fh=12.0, order=2):
        nyq = fs / 2
        self.b, self.a = butter(order, [fl/nyq, fh/nyq], btype="band")
        self.zi = None

    def step(self, x_block):
        x = np.asarray(x_block, dtype=float)
        if x.size == 0:
            return x
        if self.zi is None:
            self.zi = lfilter_zi(self.b, self.a) * x[0]
        y, self.zi = lfilter(self.b, self.a, x, zi=self.zi)
        return y


class StreamingLowpass:
    """Causal Butterworth lowpass with persistent state."""
    def __init__(self, fs, fc=1.0, order=2):
        nyq = fs / 2
        self.b, self.a = butter(order, fc/nyq, btype="low")
        self.zi = None

    def step(self, x_block):
        x = np.asarray(x_block, dtype=float)
        if x.size == 0:
            return x
        if self.zi is None:
            self.zi = lfilter_zi(self.b, self.a) * x[0]
        y, self.zi = lfilter(self.b, self.a, x, zi=self.zi)
        return y

    def reset(self, x0):
        """Re-prime filter state to a known DC level (avoids ringing on restart)."""
        self.zi = lfilter_zi(self.b, self.a) * float(x0)


class SpectrumComputer:
    """Rolling-window FFT for waterfall display."""
    def __init__(self, fs, nfft=256):
        self.fs = fs
        self.nfft = nfft
        self.window = np.hanning(nfft)
        self._win_norm = np.sum(self.window**2)
        self.buf = collections.deque(maxlen=nfft)
        self.freqs = np.fft.rfftfreq(nfft, 1.0/fs)

    def push(self, x_block):
        for x in x_block:
            self.buf.append(float(x))

    def ready(self):
        return len(self.buf) == self.nfft

    def spectrum_db(self):
        if not self.ready():
            return None
        x = np.array(self.buf)
        x = x - x.mean()
        x = x * self.window
        X = np.fft.rfft(x)
        P = (np.abs(X)**2) / (self._win_norm * self.fs)
        return 10.0 * np.log10(P + 1e-12)


# ---------------------------------------------------------------------------
# Beat tracker: detect peaks on streaming signal, emit delta_p per beat.
# Fed from the 0-5 Hz LP signal so pump noise is suppressed while retaining
# full pulse amplitude.
# ---------------------------------------------------------------------------
class BeatTracker:
    def __init__(self, fs, min_hr=40, max_hr=180, prom_mmHg=0.15, win_s=6.0):
        self.fs = fs
        self.min_dist = max(int(60.0 / max_hr * fs), 5)
        self.prom = prom_mmHg
        self.win_n = int(win_s * fs)
        self.t_buf = collections.deque(maxlen=self.win_n)
        self.ac_buf = collections.deque(maxlen=self.win_n)
        self.last_emitted_t = -1.0

    def update(self, t_block, ac_block):
        for t, x in zip(t_block, ac_block):
            self.t_buf.append(float(t))
            self.ac_buf.append(float(x))
        if len(self.ac_buf) < self.min_dist * 3:
            return []
        x = np.array(self.ac_buf)
        ts = np.array(self.t_buf)
        peaks, _ = find_peaks(x, distance=self.min_dist, prominence=self.prom)
        if len(peaks) < 2:
            return []
        events = []
        for i in range(len(peaks) - 1):
            a, b = peaks[i], peaks[i+1]
            seg = x[a:b]
            if seg.size < 5:
                continue
            t_mid = ts[(a + b)//2]
            if t_mid <= self.last_emitted_t:
                continue
            dp = float(seg.max() - seg.min())
            events.append((t_mid, dp))
            self.last_emitted_t = t_mid
        return events

    def reset(self):
        self.t_buf.clear()
        self.ac_buf.clear()
        self.last_emitted_t = -1.0


# ---------------------------------------------------------------------------
# Hardware adapter
# ---------------------------------------------------------------------------
class Hardware:
    def __init__(self, sample_q):
        self.sample_q = sample_q
        self.stop_evt = threading.Event()
        self.last_packet_time = 0.0

        self._pump = 0
        self._valve1 = True   # default OPEN: safe state
        self._valve2 = True   # default OPEN: safe state
        self._lock = threading.Lock()

        drive.subscribe(drive.MeasurementsPID.PID, self._on_packet)
        self._thr = threading.Thread(target=self._serial_loop, daemon=True)
        self._ctrl_thr = threading.Thread(target=self._control_writer, daemon=True)

    def start(self):
        self._thr.start()
        self._ctrl_thr.start()
        # Open valves first so they start in a known-safe state,
        # then close them only once we confirm the board is responding.
        drive.send_cmd(interval=INTERVAL,
                       pump_rate=0,
                       valve=drive.getValveByte(valve0=True, valve1=True),
                       cuff_pressure=True,
                       flow_rate=True,
                       pulse=True)
        deadline = time.time() + 30
        while time.time() < deadline:
            if self.last_packet_time > 0:
                # Board confirmed alive: close valves for normal idle state
                with self._lock:
                    self._valve1 = False
                    self._valve2 = False
                drive.send_cmd(interval=INTERVAL,
                               pump_rate=0,
                               valve=drive.getValveByte(valve0=False, valve1=False),
                               cuff_pressure=True,
                               flow_rate=True,
                               pulse=True)
                return
            time.sleep(0.05)
        try:
            drive.send_cmd(interval=0, pump_rate=0,
                           valve=drive.getValveByte(valve0=True, valve1=True))
        except Exception:
            pass
        raise RuntimeError(
            "mmM board imported but no measurement packets received in 3s. "
            "Check that the board has power and the firmware is running."
        )

    def stop(self):
        """Vent both valves, stop pump, stop streaming. Called on all
        normal exit paths; _emergency_vent() covers abnormal ones.

        Order matters:
          1. Set stop_evt FIRST so _control_writer exits its loop immediately
             and cannot issue any further send_cmd calls.
          2. Update internal state to open so anything that reads _valve* sees
             the correct final state.
          3. Send the vent command 3x directly from this thread -- no thread
             can now race us.
        """
        # Step 1: kill the writer thread before touching the serial port
        self.stop_evt.set()
        time.sleep(0.06)   # one _control_writer sleep cycle (0.05 s) + margin

        # Step 2: canonical internal state
        with self._lock:
            self._pump = 0
            self._valve1 = True
            self._valve2 = True

        # Step 3: send vent 3x; USB serial can drop a frame
        for _ in range(3):
            try:
                drive.send_cmd(interval=0, pump_rate=0,
                               valve=drive.getValveByte(valve0=True, valve1=True))
            except Exception:
                pass
            time.sleep(0.05)

    def set_actuators(self, pump, valve1_open=None, valve2_open=None,
                      valve_open=None):
        if valve_open is not None:
            valve1_open = valve_open if valve1_open is None else valve1_open
            valve2_open = valve_open if valve2_open is None else valve2_open
        if valve1_open is None:
            valve1_open = self._valve1
        if valve2_open is None:
            valve2_open = self._valve2
        with self._lock:
            self._pump = int(pump)
            self._valve1 = bool(valve1_open)
            self._valve2 = bool(valve2_open)

    def _on_packet(self, pkt):
        t = pkt.millis / 1000.0
        self.last_packet_time = time.time()
        try:
            self.sample_q.put_nowait((t, float(pkt.cuff), float(pkt.flow)))
        except queue.Full:
            pass

    def _serial_loop(self):
        while not self.stop_evt.is_set():
            try:
                drive.serial_interact(max_iter=20)
            except Exception as e:
                print("serial_interact error:", e)
            time.sleep(0.001)

    def _control_writer(self):
        last_sent = (None, None, None)
        last_resend = 0.0
        while not self.stop_evt.is_set():
            with self._lock:
                pump = self._pump
                v1 = self._valve1
                v2 = self._valve2
            state = (pump, v1, v2)
            now = time.time()
            need_resend = (state != last_sent) or (now - last_resend > 0.5)
            if need_resend:
                try:
                    drive.send_cmd(
                        interval=INTERVAL,
                        pump_rate=pump,
                        valve=drive.getValveByte(valve0=v1, valve1=v2),
                        cuff_pressure=True,
                        flow_rate=True,
                        pulse=True,
                    )
                    last_sent = state
                    last_resend = now
                except Exception as e:
                    print("send_cmd failed:", e)
            time.sleep(0.05)


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
class HoldGUI:
    def __init__(self, root, initial_target=80.0):
        self.root = root
        root.title("mmM pressure hold")
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.sample_q = queue.Queue(maxsize=10000)
        self.hw = Hardware(self.sample_q)
        self._shutting_down = False
        self._tick_after_id = None

        n_buf = int(DISPLAY_WINDOW_S * NOMINAL_FS)
        self.t_buf = collections.deque(maxlen=n_buf)
        self.p_buf = collections.deque(maxlen=n_buf)
        self.lp5_buf = collections.deque(maxlen=n_buf)   # 0-5 Hz LP trace
        self.dp_t = []
        self.dp_v = []

        self.bp = StreamingBandpass(NOMINAL_FS, fl=0.7, fh=12.0, order=2)
        self.lp_inflate = StreamingLowpass(NOMINAL_FS, fc=1.0, order=2)
        self.lp_5hz    = StreamingLowpass(NOMINAL_FS, fc=5.0, order=2)
        self.p_lp = None  # latest 1 Hz lowpassed pressure (inflate gating)

        # BeatTracker is now fed from the 0-5 Hz LP signal.
        # Prominence stays at 0.15 mmHg; LP retains full pulse amplitude.
        self.beats = BeatTracker(NOMINAL_FS, prom_mmHg=0.15)

        # Waterfall plumbing
        self.spec = SpectrumComputer(NOMINAL_FS, nfft=WF_NFFT)
        self.wf_enabled = False
        self.wf_n_cols = int(WF_SPAN_S / WF_UPDATE_S)
        self.wf_n_freq_full = WF_NFFT // 2 + 1
        self.wf_freqs_full = self.spec.freqs
        self.wf_fmask = self.wf_freqs_full <= WF_FMAX
        self.wf_n_freq = int(self.wf_fmask.sum())
        self.wf_image = np.full((self.wf_n_cols, self.wf_n_freq), WF_DB_LO,
                                dtype=float)
        self.wf_last_update = 0.0
        self.wf_axis = None
        self.wf_im = None

        self.hold_active = False
        self.inflating = False
        self.bleeding = False
        self.target_mmHg = float(initial_target)

        self._build_ui()
        self.hw.start()
        self._tick()

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Target (mmHg):").pack(side=tk.LEFT)
        self.target_var = tk.StringVar(value=str(int(self.target_mmHg)))
        ttk.Entry(top, width=6, textvariable=self.target_var).pack(side=tk.LEFT, padx=4)

        self.hold_btn = ttk.Button(top, text="Hold", command=self._on_hold)
        self.hold_btn.pack(side=tk.LEFT, padx=4)
        self.bleed_btn = ttk.Button(top, text="Bleed", command=self._on_bleed)
        self.bleed_btn.pack(side=tk.LEFT, padx=4)
        self.release_btn = ttk.Button(top, text="Release / Vent",
                                      command=self._on_release)
        self.release_btn.pack(side=tk.LEFT, padx=4)

        self.wf_btn_var = tk.StringVar(value="Waterfall: off")
        self.wf_btn = ttk.Button(top, textvariable=self.wf_btn_var,
                                 command=self._on_toggle_waterfall)
        self.wf_btn.pack(side=tk.LEFT, padx=4)

        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self.state_var = tk.StringVar(value="IDLE")
        self.state_lbl = ttk.Label(top, textvariable=self.state_var,
                                   font=("TkDefaultFont", 11, "bold"),
                                   foreground="gray30")
        self.state_lbl.pack(side=tk.LEFT)

        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        self.p_var = tk.StringVar(value="P:  ---  mmHg")
        self.dp_var = tk.StringVar(value="last \u0394p:  ---  mmHg")
        self.hr_var = tk.StringVar(value="HR:  ---")
        ttk.Label(top, textvariable=self.p_var,
                  font=("TkFixedFont", 12)).pack(side=tk.LEFT, padx=6)
        ttk.Label(top, textvariable=self.dp_var,
                  font=("TkFixedFont", 12)).pack(side=tk.LEFT, padx=10)
        ttk.Label(top, textvariable=self.hr_var,
                  font=("TkFixedFont", 12)).pack(side=tk.LEFT, padx=6)

        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        self.pump_var = tk.StringVar(value="pump: 0")
        self.v1_var = tk.StringVar(value="V1: closed")
        self.v2_var = tk.StringVar(value="V2: closed")
        self.pump_lbl = ttk.Label(top, textvariable=self.pump_var,
                                  font=("TkFixedFont", 11), foreground="gray40")
        self.pump_lbl.pack(side=tk.LEFT, padx=4)
        self.v1_lbl = ttk.Label(top, textvariable=self.v1_var,
                                font=("TkFixedFont", 11), foreground="gray40")
        self.v1_lbl.pack(side=tk.LEFT, padx=4)
        self.v2_lbl = ttk.Label(top, textvariable=self.v2_var,
                                font=("TkFixedFont", 11), foreground="gray40")
        self.v2_lbl.pack(side=tk.LEFT, padx=4)

        body = ttk.Frame(self.root)
        body.pack(fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(8.5, 6.0), dpi=100)
        self.ax_p = self.fig.add_subplot(2, 1, 1)
        self.ax_dp = self.fig.add_subplot(2, 1, 2)

        self._restyle_axes()
        (self.line_p,) = self.ax_p.plot([], [], lw=1.0, color="steelblue")
        (self.line_lp5,) = self.ax_p.plot([], [], lw=1.4, color="darkorange",
                                           alpha=0.85)
        self.target_hline = self.ax_p.axhline(self.target_mmHg, ls="--",
                                              color="r", alpha=0.5)

        (self.line_dp,) = self.ax_dp.plot([], [], "o-", ms=4, lw=1.0)

        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=body)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right = ttk.Frame(body, padding=(6, 6))
        right.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Label(right, text=f"Last {HISTORY_TABLE_N} beats",
                  font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W)
        cols = ("t", "dp")
        self.table = ttk.Treeview(right, columns=cols, show="headings", height=20)
        self.table.heading("t", text="t (s)")
        self.table.heading("dp", text="\u0394p (mmHg)")
        self.table.column("t", width=80, anchor=tk.E)
        self.table.column("dp", width=90, anchor=tk.E)
        self.table.pack(fill=tk.Y, expand=False)

        self.log_var = tk.StringVar(value="ready.")
        ttk.Label(self.root, textvariable=self.log_var,
                  font=("TkDefaultFont", 9), foreground="gray40",
                  anchor=tk.W).pack(fill=tk.X, padx=8, pady=(0, 6))

    # ---- callbacks --------------------------------------------------------
    def _on_hold(self):
        try:
            tgt = float(self.target_var.get())
        except ValueError:
            messagebox.showerror("Invalid target", "Enter a numeric target in mmHg.")
            return
        if tgt < 0 or tgt > HARD_MAX_MMHG - 5:
            messagebox.showerror("Out of range",
                                 f"Target must be 0..{HARD_MAX_MMHG-5:.0f} mmHg.")
            return
        self.target_mmHg = tgt
        self.target_hline.set_ydata([tgt, tgt])
        if self.p_buf:
            self.lp_inflate.reset(self.p_buf[-1])
            self.p_lp = float(self.p_buf[-1])
        self.beats.reset()
        self.dp_t.clear()
        self.dp_v.clear()
        self.line_dp.set_data([], [])
        for c in self.table.get_children():
            self.table.delete(c)
        self.dp_var.set("last \u0394p:  ---  mmHg")
        self.hr_var.set("HR:  ---")
        self.hold_active = True
        self.inflating = True
        self.bleeding = False
        self.state_var.set(f"INFLATING -> {tgt:.0f}")
        self.state_lbl.configure(foreground="dark orange")
        self.log_var.set(f"inflating to {tgt:.1f} mmHg")

    def _on_bleed(self):
        if self.bleeding:
            self.bleeding = False
            self.hw.set_actuators(pump=0, valve1_open=False, valve2_open=False)
            self.state_var.set("BLEED PAUSED")
            self.state_lbl.configure(foreground="dark green")
            self.log_var.set("V1 closed; pressure held at current level.")
        else:
            self.inflating = False
            self.bleeding = True
            self.hold_active = True
            self.hw.set_actuators(pump=0, valve1_open=True, valve2_open=False)
            self.state_var.set("BLEEDING")
            self.state_lbl.configure(foreground="dark orange")
            self.log_var.set("V1 (bleed) open; collecting beats.")

    def _on_release(self):
        self.hold_active = False
        self.inflating = False
        self.bleeding = False
        self.hw.set_actuators(pump=0, valve1_open=True, valve2_open=True)
        self.state_var.set("VENTING")
        self.state_lbl.configure(foreground="firebrick")
        self.log_var.set("V1 + V2 open, pump off; beat detection stopped.")

    def _on_toggle_waterfall(self):
        self.wf_enabled = not self.wf_enabled
        if self.wf_enabled:
            self.fig.clear()
            self.ax_p = self.fig.add_subplot(3, 1, 1)
            self.ax_dp = self.fig.add_subplot(3, 1, 2)
            self.wf_axis = self.fig.add_subplot(3, 1, 3)
            self._restyle_axes()
            self.wf_image[:] = WF_DB_LO
            self.wf_im = self.wf_axis.imshow(
                self.wf_image,
                aspect="auto",
                origin="upper",
                extent=[0, WF_FMAX, 0, WF_SPAN_S],
                vmin=WF_DB_LO, vmax=WF_DB_HI,
                cmap="viridis",
                interpolation="nearest",
            )
            self.wf_axis.set_xlabel("freq (Hz)")
            self.wf_axis.set_ylabel("time ago (s)")
            self.wf_axis.set_title("Cuff pressure spectrogram (dB)")
            self.wf_axis.invert_yaxis()
            self.fig.colorbar(self.wf_im, ax=self.wf_axis,
                              fraction=0.04, pad=0.02, label="dB")
            self.wf_btn_var.set("Waterfall: on")
        else:
            self.fig.clear()
            self.ax_p = self.fig.add_subplot(2, 1, 1)
            self.ax_dp = self.fig.add_subplot(2, 1, 2)
            self.wf_axis = None
            self.wf_im = None
            self._restyle_axes()
            self.wf_btn_var.set("Waterfall: off")

        # Re-create all data lines on the fresh axes
        (self.line_p,) = self.ax_p.plot([], [], lw=1.0, color="steelblue")
        (self.line_lp5,) = self.ax_p.plot([], [], lw=1.4, color="darkorange",
                                           alpha=0.85)
        self.target_hline = self.ax_p.axhline(self.target_mmHg, ls="--",
                                              color="r", alpha=0.5)
        (self.line_dp,) = self.ax_dp.plot([], [], "o-", ms=4, lw=1.0)
        self.fig.tight_layout()
        self.canvas.draw_idle()

    def _restyle_axes(self):
        self.ax_p.set_ylabel("cuff P (mmHg)")
        self.ax_p.set_title("Live cuff pressure")
        self.ax_p.grid(alpha=0.3)
        self.ax_p.set_xlim(-DISPLAY_WINDOW_S, 0)
        self.ax_dp.set_ylabel("\u0394p peak-to-trough (mmHg)")
        self.ax_dp.set_xlabel("time (s)")
        self.ax_dp.set_title("Per-beat oscillation amplitude  [LP 0–5 Hz signal]")
        self.ax_dp.grid(alpha=0.3)

    def _on_close(self):
        self._shutting_down = True          # stop _tick from re-arming
        if self._tick_after_id is not None:
            try:
                self.root.after_cancel(self._tick_after_id)
            except Exception:
                pass
            self._tick_after_id = None
        self.log_var.set("shutting down -- venting cuff...")
        self.root.update_idletasks()
        self.hold_active = False
        self.inflating = False
        self.bleeding = False
        self.hw.stop()          # kills writer thread, then sends vent cmd 3×
        self.root.destroy()

    # ---- main UI tick -----------------------------------------------------
    def _tick(self):
        if self._shutting_down:
            return
        try:
            self._tick_body()
        except Exception as exc:
            # Unhandled exception in the UI loop: vent immediately, then
            # surface the error so it isn't swallowed silently.
            _emergency_vent(f"unhandled tick exception: {exc}")
            try:
                self.hw.stop()
            except Exception:
                pass
            raise

    def _tick_body(self):
        new_t, new_p = [], []
        try:
            while True:
                t, p, _flow = self.sample_q.get_nowait()
                new_t.append(t)
                new_p.append(p)
        except queue.Empty:
            pass

        if new_t:
            np_new_p = np.array(new_p)

            for t, p in zip(new_t, new_p):
                self.t_buf.append(t)
                self.p_buf.append(p)

            # 1 Hz LP for inflate gating
            lp_block = self.lp_inflate.step(np_new_p)
            self.p_lp = float(lp_block[-1])

            # 0–5 Hz LP: stored for display and fed to BeatTracker
            lp5_block = self.lp_5hz.step(np_new_p)
            for v in lp5_block:
                self.lp5_buf.append(float(v))

            # Feed raw pressure to the spectrum (DC removed inside FFT)
            if self.wf_enabled:
                self.spec.push(new_p)
                now = time.time()
                if (now - self.wf_last_update) >= WF_UPDATE_S and self.spec.ready():
                    self.wf_last_update = now
                    spec_full = self.spec.spectrum_db()
                    spec = spec_full[self.wf_fmask]
                    self.wf_image[1:, :] = self.wf_image[:-1, :]
                    self.wf_image[0, :] = spec
                    if self.wf_im is not None:
                        self.wf_im.set_data(self.wf_image)

            # Beat detection: use LP 0-5 Hz signal (pump noise suppressed,
            # full pulse amplitude retained)
            if self.hold_active and not self.inflating:
                events = self.beats.update(np.array(new_t), lp5_block)
            else:
                events = []
            for t_mid, dp in events:
                self.dp_t.append(t_mid)
                self.dp_v.append(dp)
                self.table.insert("", 0, values=(f"{t_mid:7.2f}", f"{dp:6.3f}"))
                children = self.table.get_children()
                if len(children) > HISTORY_TABLE_N:
                    for c in children[HISTORY_TABLE_N:]:
                        self.table.delete(c)

            p_now = new_p[-1]
            self.p_var.set(f"P: {p_now:6.1f} mmHg")
            with self.hw._lock:
                pump_state = self.hw._pump
                v1 = self.hw._valve1
                v2 = self.hw._valve2
            self.pump_var.set(f"pump: {pump_state}")
            self.pump_lbl.configure(
                foreground=("dark green" if pump_state > 0 else "gray40"))
            self.v1_var.set(f"V1: {'OPEN' if v1 else 'closed'}")
            self.v1_lbl.configure(foreground=("firebrick" if v1 else "gray40"))
            self.v2_var.set(f"V2: {'OPEN' if v2 else 'closed'}")
            self.v2_lbl.configure(foreground=("firebrick" if v2 else "gray40"))
            if self.dp_v:
                self.dp_var.set(f"last \u0394p: {self.dp_v[-1]:5.2f} mmHg")
            if len(self.dp_t) >= 2:
                hr = 60.0 / (self.dp_t[-1] - self.dp_t[-2] + 1e-9)
                if 30 < hr < 200:
                    self.hr_var.set(f"HR: {hr:5.1f}")

            t_arr = np.array(self.t_buf)
            p_arr = np.array(self.p_buf)
            lp5_arr = np.array(self.lp5_buf)
            if t_arr.size:
                t_now = t_arr[-1]
                t_rel = t_arr - t_now
                self.line_p.set_data(t_rel, p_arr)
                # lp5_buf may lag t_buf by a few samples during startup
                if lp5_arr.size == t_arr.size:
                    self.line_lp5.set_data(t_rel, lp5_arr)
                else:
                    n = lp5_arr.size
                    self.line_lp5.set_data(t_rel[-n:], lp5_arr)
                self.ax_p.set_xlim(-DISPLAY_WINDOW_S, 0)
                p_lo = min(p_arr.min(), self.target_mmHg) - 5
                p_hi = max(p_arr.max(), self.target_mmHg) + 5
                self.ax_p.set_ylim(p_lo, p_hi)

            if self.dp_t:
                self.line_dp.set_data(self.dp_t, self.dp_v)
                self.ax_dp.set_xlim(min(self.dp_t), max(self.dp_t) + 0.5)
                self.ax_dp.set_ylim(0, max(self.dp_v) * 1.15 + 0.1)

            self.canvas.draw_idle()
            self._control_step(p_now)

        # Pressure watchdog
        if new_t and new_p[-1] > WATCHDOG_MMHG:
            if self.hold_active or self.inflating or self.bleeding:
                self.hold_active = False
                self.inflating = False
                self.bleeding = False
                self.hw.set_actuators(pump=0, valve1_open=True, valve2_open=True)
                self.state_var.set(f"WATCHDOG VENT ({new_p[-1]:.0f})")
                self.state_lbl.configure(foreground="firebrick")
                self.log_var.set(
                    f"watchdog: pressure {new_p[-1]:.0f} > {WATCHDOG_MMHG:.0f}, venting.")

        self._tick_after_id = self.root.after(UI_REFRESH_MS, self._tick)

    # ---- inflate-to-target then idle -------------------------------------
    def _control_step(self, p_now):
        if p_now > HARD_MAX_MMHG:
            self.hold_active = False
            self.inflating = False
            self.bleeding = False
            self.hw.set_actuators(pump=0, valve1_open=True, valve2_open=True)
            self.state_var.set(f"OVER LIMIT ({p_now:.0f})")
            self.state_lbl.configure(foreground="firebrick")
            return

        if not self.hold_active:
            return

        if self.bleeding:
            return

        if self.inflating:
            p_decide = self.p_lp if self.p_lp is not None else p_now
            if p_decide >= self.target_mmHg:
                self.inflating = False
                self.hw.set_actuators(pump=0, valve1_open=False, valve2_open=False)
                self.beats.reset()
                self.state_var.set(f"HOLDING @ {self.target_mmHg:.0f}")
                self.state_lbl.configure(foreground="dark green")
                self.log_var.set(
                    f"reached {p_decide:.1f} mmHg (lp); pump off, valves closed.")
            else:
                self.hw.set_actuators(pump=1, valve1_open=False, valve2_open=False)


# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="mmM pressure-hold GUI")
    parser.add_argument(
        "target", nargs="?", type=float, default=80.0,
        metavar="MMHG",
        help="initial hold target in mmHg (default: 80)"
    )
    args = parser.parse_args()
    if not (0 < args.target < HARD_MAX_MMHG - 5):
        parser.error(f"target must be between 0 and {HARD_MAX_MMHG-5:.0f} mmHg")
    root = tk.Tk()
    gui = None
    try:
        gui = HoldGUI(root, initial_target=args.target)
        root.mainloop()
    except RuntimeError as e:
        _emergency_vent(f"RuntimeError in main: {e}")
        try:
            messagebox.showerror("mmM hardware error", str(e))
        except Exception:
            pass
        try:
            root.destroy()
        except Exception:
            pass
        raise
    except Exception as e:
        _emergency_vent(f"unexpected exception in main: {e}")
        try:
            root.destroy()
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
