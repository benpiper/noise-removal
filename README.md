# Noise Removal Tool

A professional Python application for dynamic background noise removal from audio files. Automatically detects and removes noise without requiring users to manually select noise samples.

## Features

- **Automatic Noise Detection**: Analyzes the first second of audio to profile background noise
- **Non-Stationary Noise Reduction**: Adapts to changing noise patterns throughout the audio
- **Intuitive Controls**: Four tunable parameters optimized for speech (Threshold, Reduction Amount, Frequency Smoothing, Time Smoothing)
- **Preview Capability**: A/B compare original vs processed audio before processing the full file
- **Multiple Format Support**: WAV, FLAC, MP3, M4A
- **Responsive UI**: Background threading keeps interface responsive during processing
- **Professional Quality**: Uses spectral gating algorithm for natural-sounding results

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone or download this repository

2. Navigate to the project directory:
```bash
cd noise-removal
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
python main.py
```

### Workflow

1. **Open File**: Click "File → Open" or use the File menu to load an audio file
   - Supported formats: WAV, FLAC, MP3, M4A
   - File information (sample rate, duration) is displayed

2. **Adjust Parameters** (Parameters tab):
   - **Threshold**: Controls sensitivity to noise (0-100)
     - Lower values = more aggressive noise removal
     - Higher values = preserve more original audio
   - **Reduction Amount**: How much to reduce detected noise (0-100)
     - Lower values = subtle reduction
     - Higher values = aggressive reduction
   - **Frequency Smoothing**: Spectral smoothing (0-100)
     - Affects frequency-domain smoothness
   - **Time Smoothing**: Temporal smoothing (0-100)
     - Affects how smoothly the effect changes over time
   - Click "Reset to Defaults" to restore optimal speech settings

3. **Preview** (Preview tab):
   - Set start time and duration for preview segment (default: first 5 seconds)
   - Click "Play Original" to hear unprocessed audio
   - Click "Play Processed" to process and play segment with current parameters
   - Compare the two to verify the effect
   - Click "Stop" to stop playback

4. **Process Full File**:
   - Once satisfied with preview settings, click "Process Full File"
   - Progress bar shows processing status
   - Processing completes automatically

5. **Save**:
   - Click "Save Processed Audio"
   - Choose output format (WAV recommended, FLAC supported)
   - Select save location

## Default Parameters

The application uses speech-optimized defaults:

| Parameter | Default | Effect |
|-----------|---------|--------|
| Threshold | 50 | Balanced noise detection |
| Reduction | 75 | Strong but natural-sounding |
| Freq Smoothing | 45 | Mid-range smoothing |
| Time Smoothing | 40 | Subtle temporal smoothing |

## Performance

- **Preview Generation**: < 1 second for 5-second segment
- **Full File Processing**: ~2-5 seconds per minute of audio
- **Memory Usage**: ~2-3x the audio file size during processing

## Architecture

### Core Processing (`src/core/`)

- **AudioLoader**: Load/save audio files with format conversion
- **NoiseProfiler**: Automatically detect noise profile
- **NoiseReducer**: Apply spectral gating noise reduction
- **AudioProcessor**: Coordinate the processing pipeline

### GUI (`src/gui/`)

- **MainWindow**: Primary application window with menus and layout
- **ControlPanel**: Parameter sliders for noise reduction tuning
- **PreviewControls**: Audio playback and preview region selection

### Workers (`src/workers/`)

- **ProcessingWorker**: Background thread for responsive UI during processing

## Technical Details

### Noise Reduction Algorithm

Uses `noisereduce` library with non-stationary spectral gating:
- Adapts to changing background noise
- Preserves speech clarity and natural timbre
- Automatic noise profiling from audio start

### Audio I/O

- **Loading**: librosa (flexible format support)
- **Saving**: soundfile (high quality)
- **Playback**: sounddevice

### GUI Framework

PyQt6 for professional, feature-rich interface with native look and feel

## Troubleshooting

### No Sound During Preview

- Ensure your system audio is working
- Check audio device configuration
- Try closing and reopening the application

### Processing Takes Too Long

- Close other applications to free up CPU
- Processing time depends on audio length and CPU speed
- Progress bar shows current status

### Poor Quality Results

- Try adjusting parameters:
  - Lower Threshold for more aggressive noise removal
  - Increase Reduction Amount for stronger effect
  - Adjust Frequency/Time Smoothing for natural sound
- Ensure the audio file contains clear noise in first second

## Future Enhancements

- Waveform visualization
- Advanced noise profiling modes
- Preset system for parameter configurations
- Batch processing
- Real-time processing from microphone input
- Spectrogram visualization

## License

This software is provided as-is for personal and commercial use.

## Support

For issues or questions, please check the code comments and documentation or modify the application to suit your needs.
