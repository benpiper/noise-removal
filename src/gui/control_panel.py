"""Parameter control panel with sliders"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSlider,
                             QLabel, QPushButton, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from ..utils.config import PARAM_DEFAULTS


class ControlPanel(QWidget):
    """Slider controls for noise reduction parameters"""

    parameters_changed = pyqtSignal(dict)  # Emits dict with current parameters

    def __init__(self):
        super().__init__()
        self.sliders = {}
        self.value_labels = {}
        self._setup_ui()

    def _setup_ui(self):
        """Create slider controls"""
        main_layout = QVBoxLayout()

        # Create grid for sliders
        grid = QGridLayout()

        params = [
            ('threshold', 'Threshold', 'Controls sensitivity to noise (lower = more aggressive)'),
            ('reduction', 'Reduction Amount', 'How much to reduce detected noise'),
            ('freq_smoothing', 'Frequency Smoothing', 'Spectral smoothness (higher = smoother)'),
            ('time_smoothing', 'Time Smoothing', 'Temporal smoothness (higher = smoother)'),
        ]

        for row, (key, label, tooltip) in enumerate(params):
            # Label
            label_widget = QLabel(label)
            label_widget.setToolTip(tooltip)
            grid.addWidget(label_widget, row, 0, 1, 1)

            # Slider
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(100)
            slider.setValue(PARAM_DEFAULTS[key])
            slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            slider.setTickInterval(10)
            slider.valueChanged.connect(self._on_slider_changed)
            slider.setToolTip(tooltip)
            self.sliders[key] = slider
            grid.addWidget(slider, row, 1)

            # Value label
            value_label = QLabel(str(PARAM_DEFAULTS[key]))
            value_label.setFixedWidth(40)
            self.value_labels[key] = value_label
            grid.addWidget(value_label, row, 2)

        main_layout.addLayout(grid)

        # Reset button
        reset_btn = QPushButton('Reset to Defaults')
        reset_btn.clicked.connect(self._reset_defaults)
        main_layout.addWidget(reset_btn)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def _on_slider_changed(self):
        """Handle slider value changes"""
        # Update value labels
        for key, slider in self.sliders.items():
            self.value_labels[key].setText(str(slider.value()))

        # Emit new parameters
        params = self.get_parameters()
        self.parameters_changed.emit(params)

    def _reset_defaults(self):
        """Reset all sliders to default values"""
        for key, slider in self.sliders.items():
            slider.setValue(PARAM_DEFAULTS[key])

    def get_parameters(self) -> dict:
        """Get current parameter values"""
        return {
            'threshold': self.sliders['threshold'].value(),
            'reduction': self.sliders['reduction'].value(),
            'freq_smoothing': self.sliders['freq_smoothing'].value(),
            'time_smoothing': self.sliders['time_smoothing'].value(),
        }
