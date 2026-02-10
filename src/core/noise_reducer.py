"""Noise reduction processing engine"""

import numpy as np
import noisereduce as nr
from ..utils.config import PARAM_RANGES


class NoiseReducer:
    """Apply noise reduction using spectral gating"""

    @staticmethod
    def _map_threshold(ui_value: float) -> float:
        """Map UI threshold (0-100) to algorithm multiplier (0.5-4.0)"""
        min_val, max_val = PARAM_RANGES['threshold']
        return min_val + (ui_value / 100.0) * (max_val - min_val)

    @staticmethod
    def _map_reduction(ui_value: float) -> float:
        """Map UI reduction (0-100) to prop_decrease (0.0-1.0)"""
        min_val, max_val = PARAM_RANGES['reduction']
        return min_val + (ui_value / 100.0) * (max_val - min_val)

    @staticmethod
    def _map_freq_smoothing(ui_value: float) -> float:
        """Map UI freq smoothing (0-100) to Hz (100-2000) using log scale"""
        min_val, max_val = PARAM_RANGES['freq_smoothing']
        # Log scale for more intuitive control
        log_min = np.log(min_val)
        log_max = np.log(max_val)
        log_value = log_min + (ui_value / 100.0) * (log_max - log_min)
        return np.exp(log_value)

    @staticmethod
    def _map_time_smoothing(ui_value: float) -> float:
        """Map UI time smoothing (0-100) to milliseconds (10-200)"""
        min_val, max_val = PARAM_RANGES['time_smoothing']
        return min_val + (ui_value / 100.0) * (max_val - min_val)

    @staticmethod
    def process(audio_data: np.ndarray, sample_rate: int,
                noise_sample: np.ndarray, params: dict) -> np.ndarray:
        """
        Apply noise reduction to audio.

        Args:
            audio_data: Audio to process (1D array)
            sample_rate: Sample rate in Hz
            noise_sample: Noise reference (1D array)
            params: Dictionary with keys:
                - threshold (0-100)
                - reduction (0-100)
                - freq_smoothing (0-100)
                - time_smoothing (0-100)

        Returns:
            Processed audio (1D array, same shape as input)

        Raises:
            ValueError: If parameters invalid
        """
        try:
            # Map UI parameters to algorithm parameters
            thresh_n_mult = NoiseReducer._map_threshold(params['threshold'])
            prop_decrease = NoiseReducer._map_reduction(params['reduction'])
            freq_mask_smooth_hz = NoiseReducer._map_freq_smoothing(params['freq_smoothing'])
            time_mask_smooth_ms = NoiseReducer._map_time_smoothing(params['time_smoothing'])

            # Apply noise reduction using noisereduce library
            # stationary=False for non-stationary (adaptive) noise reduction
            reduced = nr.reduce_noise(
                y=audio_data,
                sr=sample_rate,
                y_noise=noise_sample,
                stationary=False,
                thresh_n_mult_nonstationary=thresh_n_mult,
                prop_decrease=prop_decrease,
                freq_mask_smooth_hz=freq_mask_smooth_hz,
                time_mask_smooth_ms=time_mask_smooth_ms,
            )

            return reduced

        except Exception as e:
            raise ValueError(f"Noise reduction failed: {str(e)}")
