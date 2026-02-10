# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Noise Removal Tool** is a professional Python GUI application for automatic background noise removal from audio files using spectral gating. It targets speech-focused audio with automatic noise profiling and provides real-time preview capability.

## Key Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Reinstall PyQt6 if ABI issues occur
python3 -m pip install --upgrade --force-reinstall PyQt6
```

### Running the Application
```bash
# Start the GUI application
python3 main.py
```

### Testing Audio Playback
```bash
# Test if sounddevice playback works
python3 << 'EOF'
import sounddevice as sd
import numpy as np

sample_rate = 44100
duration = 2
frequency = 440
t = np.linspace(0, duration, int(sample_rate * duration))
audio = 0.3 * np.sin(2 * np.pi * frequency * t)

print(f"Default audio device: {sd.default.device}")
print(f"Device list:\n{sd.query_devices()}\n")
print("Playing test tone...")
sd.play(audio, sample_rate)
sd.wait()
EOF
```

## Architecture Overview

### Three-Layer Design

**1. Core Processing Layer** (`src/core/`)
- **AudioProcessor**: Main orchestrator that manages the entire pipeline
  - `load_file()`: Loads audio and generates noise profile
  - `generate_preview()`: Extracts segment, processes it, returns original + processed for A/B comparison
  - `process_full_file()`: Processes entire audio with progress callbacks
  - `save_processed_audio()`: Saves output file
- **AudioLoader**: Audio I/O using librosa (loading, any format) and soundfile (saving, WAV/FLAC)
- **NoiseProfiler**: Extracts first 1 second of audio as noise reference sample
- **NoiseReducer**: Wraps `noisereduce` library with parameter mapping from UI 0-100 scales to algorithm-specific ranges

**2. GUI Layer** (`src/gui/`)
- **MainWindow**: Qt6 main window with menu bar, tabs, file dialogs, and signal coordination
  - Manages file loading workflow
  - Connects all child widgets to AudioProcessor
  - Handles preview requests and full file processing via ProcessingWorker
- **ControlPanel**: Four horizontal sliders (Threshold, Reduction, Freq Smoothing, Time Smoothing)
  - Each slider is 0-100 scale
  - Emits `parameters_changed` signal when any slider moves
  - Reset to defaults button
- **PreviewControls**: Playback controls and preview region selection
  - Start time (spinbox) + Duration (spinbox) for preview segment selection
  - Play Original / Play Processed / Stop buttons
  - Manages PlaybackWorker thread for audio playback
  - Emits `request_preview` signal with start_sec, duration_sec, and optional play_original flag

**3. Threading Layer** (`src/workers/`)
- **ProcessingWorker**: QThread subclass that runs `process_full_file()` without blocking GUI
  - Emits `progress` signal (0-100%) during processing
  - Emits `finished` signal with processed audio array
  - Emits `error` signal on failure
  - Supports cancellation via `stop()` method

### Data Flow

```
User opens file
  ↓
MainWindow._on_open_file() → AudioProcessor.load_file()
  ├─ AudioLoader.load() → audio_data, sample_rate
  ├─ NoiseProfiler.estimate_noise_profile() → noise_sample (first 1 sec)
  └─ Update UI with file info

User adjusts parameters → ControlPanel.parameters_changed signal

User clicks "Play Original/Processed"
  ↓
PreviewControls.request_preview signal
  ↓
MainWindow._on_preview_requested()
  ├─ AudioProcessor.generate_preview()
  │  └─ NoiseReducer.process(segment, noise_sample, params)
  ├─ PreviewControls.set_preview_data()
  └─ PreviewControls.play_processed_segment() → PlaybackWorker

User clicks "Process Full File"
  ↓
ProcessingWorker.run()
  ├─ AudioProcessor.process_full_file(params, progress_callback)
  │  └─ NoiseReducer.process(full_audio, noise_sample, params)
  └─ Emit finished(processed_audio)

User clicks "Save"
  ↓
AudioProcessor.save_processed_audio()
```

## Parameter Mapping

All UI parameters are 0-100 scales mapped to algorithm-specific ranges:

| UI Parameter | Range | Algorithm Parameter | Maps To | Scale |
|---|---|---|---|---|
| Threshold | 0-100 | `thresh_n_mult_nonstationary` | 0.5-4.0 | Linear |
| Reduction | 0-100 | `prop_decrease` | 0.0-1.0 | Linear |
| Freq Smoothing | 0-100 | `freq_mask_smooth_hz` | 100-2000 Hz | **Logarithmic** |
| Time Smoothing | 0-100 | `time_mask_smooth_ms` | 10-200 ms | Linear |

Speech-optimized defaults: Threshold=50, Reduction=75, Freq Smoothing=45, Time Smoothing=40

## Critical Implementation Details

### Audio Playback (src/gui/preview_controls.py)
- **PlaybackWorker**: Custom QThread for background audio playback
  - Uses `sounddevice.play()` to start playback
  - Monitors elapsed time vs audio duration (since `sd.is_playing()` doesn't exist)
  - Checks stop flag every 50ms for responsive cancellation
  - Ensures audio is float32 before playback
- **Key issue fixed**: Use `wait(milliseconds)` (positional arg) not `wait(timeout=ms)` for QThread

### File Loading
- **Supported formats**: WAV, FLAC, MP3, M4A (validated in `src/utils/validators.py`)
- **Stereo to mono**: Automatic via librosa's `mono=True` parameter
- **Sample rate range**: 16-96 kHz (validated in config)

### Threading Strategy
- **Main thread**: GUI remains responsive, handles all Qt signals/slots
- **PlaybackWorker**: Handles audio playback in background
- **ProcessingWorker**: Handles full file processing in background with progress updates
- **Critical**: Never call GUI-modifying methods from worker threads; use Qt signals instead

## Common Modifications

### Adding a New Parameter
1. Add to `PARAM_DEFAULTS` and `PARAM_RANGES` in `src/utils/config.py`
2. Add slider to `ControlPanel._setup_ui()` in `src/gui/control_panel.py`
3. Add mapping function to `NoiseReducer` class in `src/core/noise_reducer.py`
4. Add to `process()` method's `noisereduce.reduce_noise()` call

### Changing Audio Formats
- Edit `SUPPORTED_FORMATS` in `src/utils/config.py`
- Edit file dialog filter in `MainWindow._on_open_file()` in `src/gui/main_window.py`

### Modifying Defaults
- `PARAM_DEFAULTS`, `PREVIEW_DURATION`, `PREVIEW_START` in `src/utils/config.py`
- Window size: `WINDOW_WIDTH`, `WINDOW_HEIGHT` in config

### Fixing Qt/Python Version Issues
- PyQt6 ABI mismatch: Force reinstall → `pip install --upgrade --force-reinstall PyQt6`
- QThread wait() syntax: Use positional arg `wait(1000)` not `wait(timeout=1000)`

## Known Limitations & Fixes Applied

### Audio Playback Issues
1. **No `sd.is_playing()` function**: Use elapsed time vs duration comparison instead
2. **QThread.wait() doesn't accept `timeout=` keyword**: Use positional argument `wait(1000)`
3. **Thread freeze on Stop**: Use timeout and force quit if necessary

### Testing Audio
- Test with short audio files first (5-30 seconds)
- Verify noise profile is extracted from first second
- Parameter defaults are optimized for speech; adjust for other audio types

## Dependencies

**Core Processing**: noisereduce (spectral gating), librosa (loading), soundfile (saving), numpy/scipy
**GUI**: PyQt6 (interface), sounddevice (playback)
**Optional**: pydub (MP3 support, may require system ffmpeg)

## File Organization

- `main.py`: Entry point, creates QApplication and MainWindow
- `src/core/`: Audio processing pipeline (no GUI dependencies)
- `src/gui/`: PyQt6 interface components
- `src/workers/`: Background threading (QThread subclasses)
- `src/utils/`: Config constants and validators
- `README.md`: User-facing documentation
- `.gitignore`: Excludes audio files, __pycache__, venv

## Future Enhancement Opportunities

- Waveform visualization (matplotlib integration)
- Preset system (save/load parameter configurations as JSON)
- Batch processing (extend ProcessingWorker to handle multiple files)
- Real-time microphone input (add audio input device selection)
- Spectrogram display (librosa + matplotlib)
