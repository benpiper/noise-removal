"""Audio effects processing including dynamic range compression"""

import numpy as np


class AudioEffects:
    """Apply various effects to audio data"""

    @staticmethod
    def apply_compression(
        audio_data: np.ndarray,
        sample_rate: int,
        threshold_db: float,
        ratio: float,
        attack_ms: float,
        release_ms: float,
        makeup_gain_db: float,
    ) -> np.ndarray:
        """
        Apply dynamic range compression to an audio signal.

        Args:
            audio_data: 1D numpy array of audio samples
            sample_rate: Sample rate in Hz
            threshold_db: Threshold in dBFS above which compression applies
            ratio: Compression ratio (e.g., 4.0 means 4:1 compression)
            attack_ms: Attack time in milliseconds
            release_ms: Release time in milliseconds
            makeup_gain_db: Gain applied after compression

        Returns:
            Compressed audio as a 1D numpy array
        """
        # Convert times to coefficients
        attack_coeffs = np.exp(-1.0 / (sample_rate * (attack_ms / 1000.0)))
        release_coeffs = np.exp(-1.0 / (sample_rate * (release_ms / 1000.0)))

        # Convert threshold and makeup gain from dB to linear
        threshold_linear = 10 ** (threshold_db / 20)
        makeup_gain_linear = 10 ** (makeup_gain_db / 20)

        compressed_audio = np.zeros_like(audio_data)
        envelope = 0.0

        print(
            f"Applying DRC (Thresh: {threshold_db}dB, Ratio: {ratio}:1, Makeup: {makeup_gain_db}dB)"
        )

        for i, sample in enumerate(audio_data):
            abs_sample = abs(sample)

            # Smooth the envelope
            if abs_sample > envelope:
                envelope = attack_coeffs * envelope + (1 - attack_coeffs) * abs_sample
            else:
                envelope = release_coeffs * envelope + (1 - release_coeffs) * abs_sample

            # Apply gain reduction if envelope is above threshold
            if envelope > threshold_linear:
                # Calculate gain reduction in dB
                env_db = 20 * np.log10(envelope + 1e-9)
                overshoot_db = env_db - threshold_db

                # Apply ratio to the overshoot
                reduced_overshoot_db = overshoot_db / ratio
                gain_reduction_db = reduced_overshoot_db - overshoot_db

                # Convert gain reduction to multiplier
                gain_linear = 10 ** (gain_reduction_db / 20)
            else:
                gain_linear = 1.0

            # Apply gain reduction and makeup gain
            compressed_audio[i] = sample * gain_linear * makeup_gain_linear

        return compressed_audio

    @staticmethod
    def apply_noise_gate(
        audio_data: np.ndarray,
        sample_rate: int,
        threshold_db: float = -40.0,
    ) -> np.ndarray:
        """
        Apply a smoothed noise gate to an audio signal to prevent crossover distortion.

        Args:
            audio_data: 1D numpy array of audio samples
            sample_rate: Sample rate in Hz
            threshold_db: Threshold in dBFS below which audio is gated (silenced)

        Returns:
            Gated audio as a 1D numpy array
        """
        print(f"Applying Noise Gate (Thresh: {threshold_db}dB)")
        from scipy.ndimage import gaussian_filter1d

        threshold_linear = 10 ** (threshold_db / 20)

        # Calculate moving RMS (10ms window)
        window_size = max(1, int(sample_rate * 0.01))
        padded = np.pad(
            audio_data, (window_size // 2, window_size - window_size // 2), mode="edge"
        )
        cumsum_sq = np.cumsum(padded**2)
        rms = np.sqrt(
            (cumsum_sq[window_size:] - cumsum_sq[:-window_size]) / window_size
        )

        # Generate hard gate based on the envelope RMS rather than instantaneous samples
        gain_mask = np.where(rms > threshold_linear, 1.0, 0.0)

        # Apply intense smoothing (approx 50ms) to the gate mask to create a gentle attack/release
        # This completely removes the 'staticky' crossover distortion during zero-crossings
        smooth_gain = gaussian_filter1d(gain_mask, sigma=sample_rate * 0.05)

        return audio_data * smooth_gain
