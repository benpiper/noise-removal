"""Pipeline coordinator for audio processing"""

import numpy as np
from typing import Optional
from scipy.signal import butter, filtfilt
from .audio_loader import AudioLoader
from .noise_profiler import NoiseProfiler
from .noise_reducer import NoiseReducer
from ..utils.config import get_format_from_extension


class AudioProcessor:
    """Coordinate audio loading, analysis, and processing for the CLI pipeline"""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}

        self.original_audio = None
        self.sample_rate = None
        self.noise_sample = None
        self.file_path = None

        # Audio candidates
        self.candidate_0 = None
        self.candidate_1 = None
        self.candidate_2 = None
        self.candidate_3 = None

    def load_file(self, file_path: str) -> bool:
        """
        Load audio file.
        """
        try:
            self.audio_data, self.sample_rate = AudioLoader.load(file_path)
            self.file_path = file_path
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def generate_candidate_0(self) -> np.ndarray:
        """
        Candidate 0: Normalize to 0 dB, apply high-pass filter > 80 Hz.
        """
        if self.audio_data is None:
            raise RuntimeError("No audio file loaded")

        print("Applying high-pass filter (> 80 Hz)...")
        nyq = 0.5 * self.sample_rate
        normal_cutoff = 80.0 / nyq
        b, a = butter(5, normal_cutoff, btype="high", analog=False)
        filtered = filtfilt(b, a, self.audio_data)

        print("Normalizing to 0 dB...")
        max_val = np.max(np.abs(filtered))
        if max_val > 0:
            filtered = filtered / max_val

        self.candidate_0 = filtered

        # Generate noise profile from candidate 0
        self.noise_sample = NoiseProfiler.estimate_noise_profile(
            self.candidate_0, self.sample_rate
        )
        return self.candidate_0

    def generate_noise_candidates(self) -> list:
        """
        Create candidates 1-3 using minimal, moderate, and aggressive noise reduction on candidate 0.
        """
        if self.candidate_0 is None:
            raise RuntimeError("Candidate 0 not generated yet")

        # Default config values if missing
        nr_conf = self.config.get("noise_reduction", {})
        min_red = nr_conf.get("minimal", 0.5) * 100
        mid_red = nr_conf.get("middle", 0.75) * 100
        agg_red = nr_conf.get("aggressive", 0.9) * 100

        presets = [
            {
                "name": "Candidate 1 (Minimal)",
                "params": {
                    "threshold": 25,
                    "reduction": min_red,
                    "freq_smoothing": 30,
                    "time_smoothing": 30,
                },
            },
            {
                "name": "Candidate 2 (Medium)",
                "params": {
                    "threshold": 50,
                    "reduction": mid_red,
                    "freq_smoothing": 45,
                    "time_smoothing": 40,
                },
            },
            {
                "name": "Candidate 3 (Aggressive)",
                "params": {
                    "threshold": 75,
                    "reduction": agg_red,
                    "freq_smoothing": 60,
                    "time_smoothing": 50,
                },
            },
        ]

        candidates = []
        for preset in presets:
            print(f"Generating {preset['name']}...")
            processed = NoiseReducer.process(
                self.candidate_0, self.sample_rate, self.noise_sample, preset["params"]
            )
            # Normalize after noise reduction to maintain levels
            max_val = np.max(np.abs(processed))
            if max_val > 0:
                processed = processed / max_val
            candidates.append(processed)

        self.candidate_1 = candidates[0]
        self.candidate_2 = candidates[1]
        self.candidate_3 = candidates[2]

        return candidates

    def generate_compression_candidates(self, base_audio: np.ndarray) -> list:
        """
        Create candidates 4-6 using minimal, moderate, and aggressive dynamic range compression
        on a previously generated base candidate.
        """
        print("Generating compression candidates...")

        comp_conf = self.config.get("compressor", {})
        c_min = comp_conf.get(
            "minimal", {"threshold_db": -20.0, "ratio": 2.0, "makeup_gain": 5.0}
        )
        c_mid = comp_conf.get(
            "middle", {"threshold_db": -30.0, "ratio": 4.0, "makeup_gain": 10.0}
        )
        c_agg = comp_conf.get(
            "aggressive", {"threshold_db": -40.0, "ratio": 8.0, "makeup_gain": 15.0}
        )

        presets = [
            {
                "name": "Candidate 4 (Minimal Comp)",
                "params": {
                    "threshold_db": c_min.get("threshold_db", -20.0),
                    "ratio": c_min.get("ratio", 2.0),
                    "attack_ms": 10.0,
                    "release_ms": 100.0,
                    "makeup_gain_db": c_min.get("makeup_gain", 5.0),
                },
            },
            {
                "name": "Candidate 5 (Medium Comp)",
                "params": {
                    "threshold_db": c_mid.get("threshold_db", -30.0),
                    "ratio": c_mid.get("ratio", 4.0),
                    "attack_ms": 5.0,
                    "release_ms": 250.0,
                    "makeup_gain_db": c_mid.get("makeup_gain", 10.0),
                },
            },
            {
                "name": "Candidate 6 (Aggressive Comp)",
                "params": {
                    "threshold_db": c_agg.get("threshold_db", -40.0),
                    "ratio": c_agg.get("ratio", 8.0),
                    "attack_ms": 5.0,
                    "release_ms": 400.0,
                    "makeup_gain_db": c_agg.get("makeup_gain", 15.0),
                },
            },
        ]

        from .audio_effects import AudioEffects

        candidates = []
        for preset in presets:
            processed = AudioEffects.apply_compression(
                base_audio, self.sample_rate, **preset["params"]
            )
            # Normalize to 0 dB
            max_val = np.max(np.abs(processed))
            if max_val > 0:
                processed = processed / max_val
            candidates.append(processed)

        return candidates

    def apply_noise_gate(
        self, audio_data: np.ndarray, threshold_db: float = -40.0
    ) -> np.ndarray:
        """Apply noise gate to audio data"""
        from .audio_effects import AudioEffects

        return AudioEffects.apply_noise_gate(audio_data, self.sample_rate, threshold_db)

    def generate_maximized_candidate(
        self, audio_data: np.ndarray, target_dbfs: float = -18.0
    ) -> np.ndarray:
        """
        Scale the given audio data to achieve the target RMS in dBFS.
        If achieving target_dbfs would cause clipping, it scales as much as possible without clipping.
        """
        print(
            f"Maximizing audio to {target_dbfs} dBFS or max possible without clipping..."
        )

        # Calculate current RMS
        rms = np.sqrt(np.mean(audio_data**2))
        if rms == 0:
            return audio_data.copy()

        current_dbfs = 20 * np.log10(rms)

        # Calculate required gain
        gain_db = target_dbfs - current_dbfs
        gain_linear = 10 ** (gain_db / 20)

        # Check for clipping
        max_peak = np.max(np.abs(audio_data))
        if max_peak * gain_linear > 1.0:
            # If the gain would cause the maximum peak to exceed 1.0,
            # calculate the maximum possible gain that won't clip.
            # Using 0.999 to be safe from floating point errors
            max_possible_gain = 0.999 / max_peak
            print(
                f"Warning: Target gain would cause clipping. Limiting gain from {gain_linear:.2f}x to {max_possible_gain:.2f}x."
            )
            gain_linear = max_possible_gain

        # Apply gain
        maximized = audio_data * gain_linear

        return maximized

    def save_processed_audio(
        self, output_path: str, audio_data: np.ndarray, format: Optional[str] = None
    ) -> bool:
        """
        Save processed audio to file.
        """
        if self.sample_rate is None:
            return False

        try:
            if format is None:
                format = get_format_from_extension(output_path)

            AudioLoader.save(output_path, audio_data, self.sample_rate, format)
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False
