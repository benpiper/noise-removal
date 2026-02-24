# Specifications

Cleanscriber is a fully-automated command line tool that finds the optimal noise reduction, equalizer settings, and audio level for highlighting and detecting speech.

# Goal

The purpose is to take spoken audio that is soft, noisy, or ambiguous, and to automatically clean it up to make the spoken audio intelligible. It is intended to be an audio repair tool that can clean up and extract meaningful transcripts from bad audio.

# Process

The process is as follows:

1. Cleanscriber normalizes the original audio to 0 dB, and applies a high-pass filter to exclude < 80 Hz frequencies. From this it generates a file known as candidate 0.
2. Cleanscriber uses Whisper to gauge the quality of the audio in candidate 0 based on confidence scores.
3. Cleanscriber uses the existing noise-removal logic with sane defaults to create three different candidate audio files from candidate 0: candidate 1 with minimal noise reduction, candidate 2 with middle-of-the-road noise reduction, and candidate 3 with aggressive noise reduction. These are called candidate_1_nr, candidate_2_nr, and candidate_3_nr.
4. Cleanscriber runs each candidate (1-3) through Whisper and keeps the candidate with the highest confidence score: the base winning candidate. (Note: the base winning candidate's and candidate 0's confidence scores are considered in this competition.)
5. Cleanscriber takes the base winning candidate and applies a noise gate (-50 dB default, configurable). This is named candidate_#_ng where # is the number of the base winning candidate.
6. Cleanscriber takes this output and uses a compressor to generate three different candidate audio files from it: candidate 4 with minimal compression, candidate 5 with middle-of-the-road compression, and candidate 6 with aggressive compression. These are called candidate_#_comp where # is the number of the respective candidate.
7. Cleanscriber normalizes candidates 4-6 to 0 dB.
8. Cleanscriber runs candidates 4-6 through Whisper and keeps the candidate with the highest confidence score: the final winning candidate. (Note: the final winning candidate's and candidate 0's confidence scores are considered in this competition also.)
9. Cleanscriber writes the final winner to disk in the same format as the original input, and it writes a text and transcript (SRT) file using the highest confidence transcript.

# Whisper model

Cleanscriber uses the smallest, most CPU-efficient model available (tiny default, configurable). If a CUDA GPU is available, Cleanscriber will use it.

Cleanscriber assumes all audio is in English.

# User Interface

Cleanscriber is meant to run with minimal user interaction, but it should estimate the time remaining for both its current task and its overall execution.

Input files are stored in the `input` folder. Output files should be placed in the `output` folder.

More information is better. Cleanscriber compares the confidence scores of different candidates, allowing the user to see how much better or worse one candidate is than other. It also retains copies of its candidate audio and transcript files, allowing the user to manually review them.

At the end of the run, Cleanscriber generates a markdown summary of the run, including the confidence scores of each candidate and the final winner, noise reduction settings, compressor settings, and noise gate settings. This summary is written to a file called `summary.md` in the `output` folder.

# Configuration file

Cleanscriber can be configured using a JSON file. The default configuration file is `config.json` in the `config` folder. The configuration file can be used to set the following parameters:

```json
{
  "input_dir": "input",
  "output_dir": "output",
  "model": "tiny",
  "noise_reduction": {
    "minimal": 0.5,
    "middle": 0.75,
    "aggressive": 0.9
  },
  "noise_gate": -50,
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
  },
  "cuda": false
}
```

# Development status

Cleanscriber is a fork of noise-removal, so there were unused or extraneous files in this repository. Unneeded files have been removed but may appear in previous commits.