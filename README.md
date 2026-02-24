# Cleanscriber

Cleanscriber is a fully-automated command line tool designed to rescue spoken audio that is soft, noisy, or ambiguous. It automatically cleans up audio using a series of dynamic noise reduction, noise gate, and compression algorithms, utilizing OpenAI's Whisper (or Faster-Whisper) to mathematically determine the best-sounding result via confidence scores.

## Features

- **Automated Audio Cleanup**: Unattended processing. Finds the optimal noise reduction and equalizer settings automatically.
- **AI-Driven Evaluation**: Generates 7 different "candidates" of the audio and uses Whisper transcripts to grade the intelligibility of each candidate.
- **Multiple NLP Models**: Supports the standard `openai-whisper` package as well as `faster-whisper` for optimized large model inference.
- **Export Transcripts**: Along with the best-sounding cleaned audio file, exports professional `.txt` and `.srt` transcripts mapped to the optimal audio.
- **Rich Reporting**: Outputs a `summary.md` detailing the confidence scores of each candidate and the exact parameters used.
- **Highly Configurable**: Control noise reduction intensity, noise gate thresholds, and compression ratios statically via JSON.

## Installation

### Prerequisites

- Python 3.8 or higher
- `ffmpeg` installed on your system path
- (Optional but Releated) CUDA Toolkit / cuDNN for GPU acceleration

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
   *(Note: This includes heavy ML dependencies like `torch`, `openai-whisper`, and `faster-whisper`.)*

## Usage

### Running the Pipeline

Cleanscriber runs automatically, taking a single input file and depositing timestamped results in the output folder.

```bash
./cleanscriber.py path/to/audio/file.mp3
```

By default, the script looks for files in the `input/` folder if a relative filename is provided, and saves all outputs into an isolated subfolder inside the `output/` directory so runs are never overwritten.

### CLI Arguments

```
usage: cleanscriber.py [-h] [--output-dir OUTPUT_DIR] [--model MODEL] input_file

positional arguments:
  input_file            Path to the noisy input audio file (defaults to looking inside ./input/)

options:
  -h, --help            show this help message and exit
  --output-dir OUTPUT_DIR
                        Directory to save the cleaned files (default: ./output)
  --model MODEL         Whisper model size (default: tiny)
```

## Configuration File

While you can pass the model via the CLI, deep customization of the audio pipeline is handled via a JSON configuration file. By default, `config/config.json` should look like this:

```json
{
  "input_dir": "input",
  "output_dir": "output",
  "model": "faster-whisper-large-v3",
  "noise_reduction": {
    "minimal": 0.5,
    "middle": 0.75,
    "aggressive": 0.9
  },
  "noise_gate": -50.0,
  "compressor": {
    "minimal": {
      "threshold_db": -20.0,
      "ratio": 2.0,
      "makeup_gain": 0.0
    },
    "middle": {
      "threshold_db": -30.0,
      "ratio": 4.0,
      "makeup_gain": 0.0
    },
    "aggressive": {
      "threshold_db": -40.0,
      "ratio": 8.0,
      "makeup_gain": 0.0
    }
  },
  "cuda": true
}
```

### Configuration Options
* **model**: Whisper model size string (`tiny`, `base`, `small`, `medium`, `large`). Prefix the model with `faster-whisper-` (e.g., `faster-whisper-large-v3`) to route the evaluation through the highly-optimized CTranslate2 backend.
* **noise_reduction**: The proportion of noise subtracted (0.0 to 1.0) for Candidates 1, 2, and 3.
* **noise_gate**: The hard dB threshold (-50 default) where audio is muted to dead silence to prevent Whisper hallucination loops.
* **compressor**: Defines the `threshold_db`, `ratio`, and `makeup_gain` across the three compression presets used to generate Candidates 4, 5, and 6.

## How It Works

1. **Candidate 0:** Normalizes the original audio to 0 dB and applies a high-pass filter (> 80 Hz).
2. **Candidates 1-3:** Applies minimal, medium, and aggressive static noise reduction.
3. **Base Evaluation:** Uses Whisper to score Candidates 0, 1, 2, and 3. The one with the highest confidence is declared the "Base Winner".
4. **Noise Gate:** Applies the configured noise gate (e.g., -50 dB) to the Base Winner.
5. **Candidates 4-6:** Applies dynamic range compression (minimal, medium, aggressive) to the gated audio and normalizes back to 0 dB.
6. **Final Evaluation:** Uses Whisper to score Candidates 4, 5, 6, and Candidate 0. The highest overall score is the final winner.
7. **Export:** The best audio is saved, along with the finalized Transcription text (`.txt`) and SubRip Subtitle (`.srt`) formats.
