"""Configuration constants"""

import soundfile as sf

# Audio format support
SUPPORTED_FORMATS = ('.wav', '.flac', '.mp3', '.m4a')  # Deprecated: use get_supported_input_formats()
MIN_SAMPLE_RATE = 16000  # 16 kHz
MAX_SAMPLE_RATE = 96000  # 96 kHz


def get_supported_input_formats() -> tuple:
    """
    Get all input formats supported by librosa.

    Returns:
        Tuple of lowercase extensions (e.g., ('.wav', '.flac', '.mp3', ...))
    """
    # Common formats supported by librosa
    # These are validated to work with librosa.load()
    common_formats = (
        '.wav', '.flac', '.mp3', '.m4a', '.ogg', '.opus',
        '.aac', '.aiff', '.aif', '.au', '.caf', '.wv', '.ape'
    )
    return common_formats


def get_supported_output_formats() -> dict:
    """
    Get all output formats supported by soundfile with their file extensions.

    Returns:
        Dict mapping file extension to soundfile format code
        Example: {'.wav': 'WAV', '.flac': 'FLAC', '.ogg': 'OGG', ...}
    """
    format_map = {}

    try:
        # Get all formats from soundfile
        available = sf.available_formats()

        # Map format codes to extensions
        extension_map = {
            'WAV': '.wav',
            'FLAC': '.flac',
            'OGG': '.ogg',
            'AIFF': '.aiff',
            'AU': '.au',
            'CAF': '.caf',
            'RAW': '.raw',
            'MAT4': '.mat',
            'MAT5': '.mat',
        }

        for format_code in available:
            # Try to find matching extension
            ext = extension_map.get(format_code)
            if ext:
                # Skip WAVEX if WAV already exists (prefer WAV)
                if format_code == 'WAVEX' and '.wav' in format_map:
                    continue
                format_map[ext] = format_code
            else:
                # Fallback: use lowercase format code as extension
                ext = f'.{format_code.lower()}'
                format_map[ext] = format_code

        # Ensure common formats use standard codes (not variants like WAVEX)
        if '.wav' in format_map and format_map['.wav'] == 'WAVEX':
            format_map['.wav'] = 'WAV'
        if '.flac' not in format_map:
            format_map['.flac'] = 'FLAC'

    except Exception:
        # Fallback to basic formats if something goes wrong
        format_map = {
            '.wav': 'WAV',
            '.flac': 'FLAC',
            '.ogg': 'OGG',
            '.aiff': 'AIFF',
            '.au': 'AU',
        }

    return format_map


def get_format_from_extension(file_path: str) -> str:
    """
    Extract soundfile format code from file extension.

    Args:
        file_path: File path or name

    Returns:
        Soundfile format code (e.g., 'WAV', 'FLAC', 'OGG')
        Returns 'WAV' as fallback if format not found
    """
    ext = '.' + file_path.rsplit('.', 1)[-1].lower() if '.' in file_path else '.wav'
    format_map = get_supported_output_formats()
    return format_map.get(ext, 'WAV')

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
