"""Manage noise reduction parameter presets"""

import json
from pathlib import Path


class PresetManager:
    """Handle saving and loading parameter presets"""

    def __init__(self):
        """Initialize preset manager"""
        self.preset_dir = Path.home() / '.noise_removal' / 'presets'
        self.preset_file = self.preset_dir / 'presets.json'
        self.preset_dir.mkdir(parents=True, exist_ok=True)
        self.presets = self._load_presets()

    def _load_presets(self) -> dict:
        """Load presets from file"""
        if self.preset_file.exists():
            try:
                with open(self.preset_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_presets(self):
        """Save presets to file"""
        try:
            with open(self.preset_file, 'w') as f:
                json.dump(self.presets, f, indent=2)
        except IOError as e:
            raise IOError(f"Failed to save presets: {e}")

    def save_preset(self, name: str, parameters: dict) -> None:
        """Save a parameter set as a preset"""
        if not name.strip():
            raise ValueError("Preset name cannot be empty")

        self.presets[name] = parameters
        self._save_presets()

    def load_preset(self, name: str) -> dict:
        """Load a preset by name"""
        if name not in self.presets:
            raise KeyError(f"Preset '{name}' not found")
        return self.presets[name].copy()

    def delete_preset(self, name: str) -> None:
        """Delete a preset"""
        if name in self.presets:
            del self.presets[name]
            self._save_presets()

    def get_preset_names(self) -> list:
        """Get list of all preset names"""
        return sorted(self.presets.keys())

    def has_presets(self) -> bool:
        """Check if any presets exist"""
        return len(self.presets) > 0
