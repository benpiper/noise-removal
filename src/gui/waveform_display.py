"""Waveform visualization widget using matplotlib"""

import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class WaveformDisplay(QWidget):
    """Display audio waveforms with matplotlib"""

    def __init__(self):
        super().__init__()
        self.sample_rate = 44100
        self.figure = Figure(figsize=(10, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self._setup_ui()

    def _setup_ui(self):
        """Create widget layout"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def display_comparison(self, original: np.ndarray, processed: np.ndarray, sample_rate: int):
        """Display original and processed waveforms side by side"""
        self.sample_rate = sample_rate
        self.figure.clear()

        # Create two subplots
        ax1 = self.figure.add_subplot(121)
        ax2 = self.figure.add_subplot(122)

        # Time axis in seconds
        time_original = np.arange(len(original)) / sample_rate
        time_processed = np.arange(len(processed)) / sample_rate

        # Plot original
        ax1.plot(time_original, original, color='#1f77b4', linewidth=0.5)
        ax1.set_title('Original Audio', fontsize=10, fontweight='bold')
        ax1.set_xlabel('Time (s)', fontsize=9)
        ax1.set_ylabel('Amplitude', fontsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(-1, 1)

        # Plot processed
        ax2.plot(time_processed, processed, color='#2ca02c', linewidth=0.5)
        ax2.set_title('Processed Audio', fontsize=10, fontweight='bold')
        ax2.set_xlabel('Time (s)', fontsize=9)
        ax2.set_ylabel('Amplitude', fontsize=9)
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(-1, 1)

        # Adjust layout
        self.figure.tight_layout()
        self.canvas.draw()

    def display_single(self, audio: np.ndarray, sample_rate: int, title: str = 'Waveform'):
        """Display single waveform"""
        self.sample_rate = sample_rate
        self.figure.clear()

        ax = self.figure.add_subplot(111)
        time = np.arange(len(audio)) / sample_rate

        ax.plot(time, audio, color='#1f77b4', linewidth=0.5)
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.set_xlabel('Time (s)', fontsize=9)
        ax.set_ylabel('Amplitude', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-1, 1)

        self.figure.tight_layout()
        self.canvas.draw()

    def clear(self):
        """Clear the display"""
        self.figure.clear()
        self.canvas.draw()
