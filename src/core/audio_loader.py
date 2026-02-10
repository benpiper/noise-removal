"""Audio file loading and saving"""

import numpy as np
import soundfile as sf
import librosa
from pathlib import Path
from typing import Tuple, Optional


class AudioLoader:
    """Handle audio file I/O operations"""

    @staticmethod
    def load(file_path: str) -> Tuple[np.ndarray, int]:
        """
        Load audio file and convert to mono.

        Args:
            file_path: Path to audio file

        Returns:
            Tuple of (audio_data, sample_rate)
            - audio_data: 1D numpy array (mono)
            - sample_rate: Sample rate in Hz

        Raises:
            FileNotFoundError: If file doesn't exist
            RuntimeError: If audio loading fails
        """
        file_path = str(file_path)

        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # Use librosa for flexible format support
            audio_data, sample_rate = librosa.load(file_path, sr=None, mono=True)
            return audio_data, sample_rate
        except Exception as e:
            raise RuntimeError(f"Failed to load audio: {str(e)}")

    @staticmethod
    def save(file_path: str, audio_data: np.ndarray, sample_rate: int,
             format: Optional[str] = None) -> None:
        """
        Save audio to file in specified format.

        Args:
            file_path: Output file path
            audio_data: 1D numpy array
            sample_rate: Sample rate in Hz
            format: Soundfile format code (e.g., 'WAV', 'FLAC', 'OGG').
                   Auto-detected from file extension if None.

        Raises:
            RuntimeError: If saving fails
        """
        file_path = str(file_path)

        try:
            # Auto-detect format from extension if not provided
            if format is None:
                from ..utils.config import get_format_from_extension
                format = get_format_from_extension(file_path)

            sf.write(file_path, audio_data, sample_rate, format=format)
        except Exception as e:
            raise RuntimeError(f"Failed to save audio: {str(e)}")

    @staticmethod
    def get_duration(audio_data: np.ndarray, sample_rate: int) -> float:
        """Get duration in seconds"""
        return len(audio_data) / sample_rate
