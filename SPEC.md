# Specifications

Cleanscriber is a fully-automated command line tool that finds the optimal noise reduction, equalizer settings, and audio level for highlighting and detecting speech.

# Goal

The purpose is to take spoken audio that is soft, noisy, or ambiguous, and to automatically clean it up to make the spoken audio intelligible.

# Process

The process is as follows:

1. Cleanscriber normalizes the original audio to 0 dB and applies a high-pass filter to exclude < 80 Hz frequencies. From this it generates a file known as candidate 0.
2. Cleanscriber uses Whisper to gauge the quality of the audio based on confidence scores.
3. Cleanscriber uses the existing noise-removal logic with sane defaults to create three different candidate audio files: candidate 1 with minimal noise reduction, candidate 2 with middle-of-the-road noise reduction, and candidate 3 with aggressive noise reduction.
4. Cleanscriber runs each candidate (1-3) through Whisper and keeps the candidate with the highest confidence score: the winning candidate. (Note: Candidate 0's confidence score is considered in this competition.)
5. Cleanscriber writes the winning candidate to disk in the same format as the original input, and it writes a text and transcript (SRT) file using the highest confidence transcript.

# Whisper model

Cleanscriber uses the smallest, most CPU-efficient model available. If a CUDA GPU is available, Cleanscriber will use it.

# User Interface

Cleanscriber is meant to run with minimal user interaction, but it should estimate the time remaining for both its current task and its overall execution.

More information is better. Cleanscriber compares the confidence scores of different candidates, allowing the user to see how much better or worse one candidate is than other. It also retains copies of its candidate files, allowing the user to manually review them.

# Development status

Cleanscriber is a fork of noise-removal, so there may be unused or extraneous files in this repository. Remove any unneeded files after the other specifications have been met.