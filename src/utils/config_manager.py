import json
import os

DEFAULT_CONFIG = {
    "input_dir": "input",
    "output_dir": "output",
    "model": "tiny",
    "noise_reduction": {"minimal": 0.5, "middle": 0.75, "aggressive": 0.9},
    "noise_gate": -40.0,
    "compressor": {
        "minimal": {"threshold_db": -20.0, "ratio": 2.0, "makeup_gain": 5.0},
        "middle": {"threshold_db": -30.0, "ratio": 4.0, "makeup_gain": 10.0},
        "aggressive": {"threshold_db": -40.0, "ratio": 8.0, "makeup_gain": 15.0},
    },
    "cuda": False,
}


def load_config(config_path="config/config.json") -> dict:
    """Load configuration from JSON file, falling back to defaults for missing keys."""
    config = DEFAULT_CONFIG.copy()

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)

            # Naive dictionary merge for top-level keys
            for k, v in user_config.items():
                if isinstance(v, dict) and k in config:
                    config[k].update(v)
                else:
                    config[k] = v
        except Exception as e:
            print(f"Warning: Failed to load {config_path} ({e}). Using defaults.")

    return config
