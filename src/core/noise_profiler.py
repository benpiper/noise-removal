"""Automatic noise profile detection"""

import numpy as np
from ..utils.config import NOISE_PROFILE_DURATION


class NoiseProfiler:
    """Detect noise profile from audio"""

    @staticmethod
    def estimate_noise_profile(audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Extract noise sample from beginning of audio.

        Assumes the first 1 second typically contains ambient noise.

        Args:
            audio_data: 1D audio array
            sample_rate: Sample rate in Hz

        Returns:
            1D numpy array containing noise sample
        """
        # Calculate number of samples for noise profile duration
        num_samples = int(NOISE_PROFILE_DURATION * sample_rate)

        # Take first portion of audio as noise sample
        noise_sample = audio_data[:num_samples]

        # If audio is shorter than profile duration, use what we have
        if len(noise_sample) < num_samples:
            noise_sample = audio_data

        return noise_sample
