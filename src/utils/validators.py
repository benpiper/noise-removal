"""Input validation utilities"""

import os
from .config import SUPPORTED_FORMATS, MIN_SAMPLE_RATE, MAX_SAMPLE_RATE


def is_valid_audio_file(file_path: str) -> bool:
    """Check if file exists and has supported audio format"""
    if not os.path.isfile(file_path):
        return False
    return file_path.lower().endswith(SUPPORTED_FORMATS)


def validate_sample_rate(sample_rate: int) -> bool:
    """Check if sample rate is within acceptable range"""
    return MIN_SAMPLE_RATE <= sample_rate <= MAX_SAMPLE_RATE


def validate_parameters(params: dict) -> bool:
    """Validate parameter values are in expected ranges"""
    required_keys = {'threshold', 'reduction', 'freq_smoothing', 'time_smoothing'}
    if not all(key in params for key in required_keys):
        return False

    for key in required_keys:
        value = params[key]
        if not isinstance(value, (int, float)) or not (0 <= value <= 100):
            return False

    return True


def format_duration(duration_seconds: float) -> str:
    """Format duration as MM:SS"""
    minutes = int(duration_seconds // 60)
    seconds = int(duration_seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"
