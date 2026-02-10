"""Pipeline coordinator for audio processing"""

import numpy as np
from typing import Callable, Tuple, Optional
from .audio_loader import AudioLoader
from .noise_profiler import NoiseProfiler
from .noise_reducer import NoiseReducer
from ..utils.config import PREVIEW_DURATION, PREVIEW_START, get_format_from_extension


class AudioProcessor:
    """Coordinate audio loading, analysis, and processing"""

    def __init__(self):
        self.audio_data = None
        self.sample_rate = None
        self.noise_sample = None
        self.file_path = None

    def load_file(self, file_path: str) -> bool:
        """
        Load audio file and generate noise profile.

        Args:
            file_path: Path to audio file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load audio
            self.audio_data, self.sample_rate = AudioLoader.load(file_path)

            # Generate noise profile
            self.noise_sample = NoiseProfiler.estimate_noise_profile(
                self.audio_data, self.sample_rate
            )

            self.file_path = file_path
            return True

        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def get_file_info(self) -> Optional[dict]:
        """Get information about loaded file"""
        if self.audio_data is None:
            return None

        duration = AudioLoader.get_duration(self.audio_data, self.sample_rate)
        return {
            'filename': self.file_path,
            'sample_rate': self.sample_rate,
            'duration': duration,
            'num_samples': len(self.audio_data),
        }

    def generate_preview(self, start_sec: float, duration_sec: float,
                         params: dict) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate preview segments for A/B comparison.

        Args:
            start_sec: Start position in seconds
            duration_sec: Duration in seconds
            params: Noise reduction parameters

        Returns:
            Tuple of (original_segment, processed_segment)

        Raises:
            RuntimeError: If no file loaded or invalid parameters
        """
        if self.audio_data is None:
            raise RuntimeError("No audio file loaded")

        # Calculate sample indices
        start_idx = int(start_sec * self.sample_rate)
        duration_idx = int(duration_sec * self.sample_rate)
        end_idx = min(start_idx + duration_idx, len(self.audio_data))

        # Extract segment
        segment = self.audio_data[start_idx:end_idx]

        # Process segment
        processed_segment = NoiseReducer.process(
            segment, self.sample_rate, self.noise_sample, params
        )

        return segment, processed_segment

    def process_full_file(self, params: dict,
                         progress_callback: Optional[Callable[[int], None]] = None
                         ) -> np.ndarray:
        """
        Process entire audio file.

        Args:
            params: Noise reduction parameters
            progress_callback: Optional callback(progress_percent) for progress updates

        Returns:
            Processed audio array

        Raises:
            RuntimeError: If no file loaded
        """
        if self.audio_data is None:
            raise RuntimeError("No audio file loaded")

        # Update progress
        if progress_callback:
            progress_callback(10)

        # Process audio
        processed = NoiseReducer.process(
            self.audio_data, self.sample_rate, self.noise_sample, params
        )

        # Update progress
        if progress_callback:
            progress_callback(100)

        return processed

    def save_processed_audio(self, output_path: str, audio_data: np.ndarray,
                            format: Optional[str] = None) -> bool:
        """
        Save processed audio to file.

        Args:
            output_path: Output file path
            audio_data: Audio to save
            format: Soundfile format code (e.g., 'WAV', 'FLAC', 'OGG').
                   Auto-detected from extension if None.

        Returns:
            True if successful, False otherwise
        """
        if self.sample_rate is None:
            return False

        try:
            # Auto-detect format if not provided
            if format is None:
                format = get_format_from_extension(output_path)

            AudioLoader.save(output_path, audio_data, self.sample_rate, format)
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False
