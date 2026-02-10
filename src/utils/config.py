"""Configuration constants"""

# Audio format support
SUPPORTED_FORMATS = ('.wav', '.flac', '.mp3', '.m4a')
MIN_SAMPLE_RATE = 16000  # 16 kHz
MAX_SAMPLE_RATE = 96000  # 96 kHz

# Noise profiling
NOISE_PROFILE_DURATION = 1.0  # seconds

# Parameter defaults (0-100 scale)
PARAM_DEFAULTS = {
    'threshold': 50,        # maps to 2.0 multiplier
    'reduction': 75,        # maps to 0.75 prop_decrease
    'freq_smoothing': 45,   # maps to ~500 Hz
    'time_smoothing': 40,   # maps to ~80 ms
}

# Parameter ranges for algorithm
PARAM_RANGES = {
    'threshold': (0.5, 4.0),
    'reduction': (0.0, 1.0),
    'freq_smoothing': (100, 2000),
    'time_smoothing': (10, 200),
}

# Preview defaults
PREVIEW_DURATION = 5.0  # seconds
PREVIEW_START = 0.0     # seconds

# GUI defaults
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600
SLIDER_WIDTH = 300
