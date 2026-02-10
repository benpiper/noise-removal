"""Audio preview and playback controls"""

import time
import numpy as np
import sounddevice as sd
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QSpinBox, QLabel, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from ..utils.config import PREVIEW_DURATION, PREVIEW_START
from .waveform_display import WaveformDisplay


class PlaybackWorker(QThread):
    """Background thread for audio playback"""

    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, audio_data: np.ndarray, sample_rate: int):
        super().__init__()
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self._stop_flag = False

    def run(self):
        """Play audio in background"""
        try:
            # Check if we should stop before starting
            if self._stop_flag:
                self.finished.emit()
                return

            # Ensure audio is float32
            audio = self.audio_data.astype(np.float32)

            # Calculate duration for playback monitoring
            duration = len(audio) / self.sample_rate
            start_time = time.time()

            # Play audio
            sd.play(audio, self.sample_rate)

            # Wait for playback to finish, but check stop flag periodically
            while time.time() - start_time < duration:
                if self._stop_flag:
                    sd.stop()
                    break
                time.sleep(0.05)  # Check every 50ms

            self.finished.emit()
        except Exception as e:
            self.error.emit(f"Playback error: {str(e)}")
            self.finished.emit()

    def stop(self):
        """Stop playback"""
        self._stop_flag = True
        sd.stop()


class PreviewControls(QWidget):
    """Controls for audio preview playback"""

    request_preview = pyqtSignal(dict)  # Emits dict with start_sec and duration_sec

    def __init__(self):
        super().__init__()
        self.playback_worker = None
        self.preview_original = None
        self.preview_processed = None
        self.waveform_display = WaveformDisplay()
        self._setup_ui()

    def _setup_ui(self):
        """Create preview controls"""
        main_layout = QVBoxLayout()

        # Preview region selector
        region_layout = QHBoxLayout()

        region_layout.addWidget(QLabel("Preview Start (seconds):"))
        self.start_spinbox = QSpinBox()
        self.start_spinbox.setMinimum(0)
        self.start_spinbox.setMaximum(3600)  # 1 hour max
        self.start_spinbox.setValue(int(PREVIEW_START))
        region_layout.addWidget(self.start_spinbox)

        region_layout.addWidget(QLabel("Duration (seconds):"))
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setMinimum(1)
        self.duration_spinbox.setMaximum(60)
        self.duration_spinbox.setValue(int(PREVIEW_DURATION))
        region_layout.addWidget(self.duration_spinbox)

        main_layout.addLayout(region_layout)

        # Playback buttons
        button_layout = QHBoxLayout()

        self.play_original_btn = QPushButton('Play Original')
        self.play_original_btn.clicked.connect(self._play_original)
        self.play_original_btn.setEnabled(False)
        button_layout.addWidget(self.play_original_btn)

        self.play_processed_btn = QPushButton('Play Processed')
        self.play_processed_btn.clicked.connect(self._request_preview)
        self.play_processed_btn.setEnabled(False)
        button_layout.addWidget(self.play_processed_btn)

        self.stop_btn = QPushButton('Stop')
        self.stop_btn.clicked.connect(self._stop_playback)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)

        main_layout.addLayout(button_layout)

        # Waveform display
        main_layout.addWidget(self.waveform_display)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def set_preview_data(self, original: np.ndarray, processed: np.ndarray):
        """Store preview segments and display waveforms"""
        self.preview_original = original
        self.preview_processed = processed
        self.play_original_btn.setEnabled(True)
        self.play_processed_btn.setEnabled(True)

        # Display waveform comparison
        sample_rate = getattr(self, '_current_sample_rate', 44100)
        self.waveform_display.display_comparison(original, processed, sample_rate)

    def set_full_audio_loaded(self, loaded: bool):
        """Enable/disable preview when audio is loaded"""
        self.start_spinbox.setEnabled(loaded)
        self.duration_spinbox.setEnabled(loaded)
        if loaded:
            self.play_original_btn.setEnabled(True)
            self.play_processed_btn.setEnabled(True)
        else:
            self.waveform_display.clear()

    def _request_preview(self, play_original: bool = False):
        """Request preview generation"""
        self.request_preview.emit({
            'start_sec': float(self.start_spinbox.value()),
            'duration_sec': float(self.duration_spinbox.value()),
            'play_original': play_original,
        })

    def _play_original(self):
        """Play original preview segment"""
        if self.preview_original is not None:
            self._play_audio(self.preview_original)
        else:
            # Generate preview if it hasn't been created yet, then play original
            self._request_preview(play_original=True)

    def _play_audio(self, audio_data: np.ndarray):
        """Play audio in background thread"""
        # Stop any existing playback
        self._stop_playback()

        # Get sample rate from the larger context (will be passed from main window)
        # For now, use a reasonable default
        sample_rate = getattr(self, '_current_sample_rate', 44100)

        self.playback_worker = PlaybackWorker(audio_data, sample_rate)
        self.playback_worker.finished.connect(self._on_playback_finished)
        self.playback_worker.error.connect(self._on_playback_error)
        self.playback_worker.start()

        self.stop_btn.setEnabled(True)
        self.play_original_btn.setEnabled(False)
        self.play_processed_btn.setEnabled(False)

    def _stop_playback(self):
        """Stop current playback"""
        if self.playback_worker is not None:
            self.playback_worker.stop()
            # Use timeout to prevent GUI freeze (1000 ms = 1 second)
            if not self.playback_worker.wait(1000):
                # Force quit if it doesn't stop within 1 second
                self.playback_worker.quit()
            self.playback_worker = None

        self.stop_btn.setEnabled(False)
        self.play_original_btn.setEnabled(True)
        self.play_processed_btn.setEnabled(True)

    def _on_playback_finished(self):
        """Handle playback completion"""
        self._stop_playback()

    def _on_playback_error(self, error_msg: str):
        """Handle playback error"""
        print(f"Playback error: {error_msg}")
        self._stop_playback()

    def set_sample_rate(self, sample_rate: int):
        """Store sample rate for playback"""
        self._current_sample_rate = sample_rate

    def play_processed_segment(self, audio_data: np.ndarray):
        """Play processed segment from main window"""
        self.preview_processed = audio_data
        self._play_audio(audio_data)
