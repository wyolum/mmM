INPUT_DIR  ='../input/'
OUTPUT_DIR ='../output/'
TMP_DIR    ='../tmp/'
MIN_PRESSURE = 10
MAX_PULSE = 3.
AMB_PRESSURE_MIN_COUNT = 2949;
AMB_PRESSURE_MAX_COUNT = 24794;
AMB_PRESSURE_MAX_MB = 2000;
AMB_COUNT_RANGE = AMB_PRESSURE_MAX_COUNT - AMB_PRESSURE_MIN_COUNT;
AMB_PRESSURE_SENSITIVITY = float(AMB_COUNT_RANGE) / AMB_PRESSURE_MAX_MB;

ABS_MIN_COUNT = 2949
ABS_MAX_COUNT = 24794
ABS_COUNT_RANGE = ABS_MAX_COUNT - ABS_MIN_COUNT;
ABS_MAX_PRESSURE_MB = 2000;
ABS_SENSITIVITY = float(ABS_COUNT_RANGE) / ABS_MAX_PRESSURE_MB

MMHG_TO_MBAR = 1.33322368
STS_T0 = -46.85;
STS_GAIN = 175.72;
PEAK_HEIGHT = .35;

STD_PRESSURE_MMHG = 760.

defaults = {
    'add_toolbar':True,
    'use_one_file': True,
    'hold_sec': 180, ### 180 300 sec?
    'run_unittests': False,
    'eps':0.3,
    'min_pressure_CC':20,
    'min_pressure_MAP': 50,
    'max_pressure':200,
    'min_hold_pressure':180,
    'high_cuttoff_hz':5,  
    'low_cuttoff_hz':.5,
    'dt':0.005,
    'n_tap':1000,
    'mad_thresh': 10., 
    'n_skip':750,
    'max_pulse_period':2.2, # seconds
    'mad_n_bad_thresh':1,
    'min_pulse_freq': .5,  # hertz (30 BPM)
    'max_pulse_freq': 3.33 # hertz (200 BPM)
}

# print '!!! n_tap', defaults['n_tap']
