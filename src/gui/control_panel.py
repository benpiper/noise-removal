"""Parameter control panel with sliders"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSlider,
                             QLabel, QPushButton, QGridLayout, QInputDialog,
                             QDialog, QListWidget, QListWidgetItem, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from ..utils.config import PARAM_DEFAULTS
from ..utils.preset_manager import PresetManager


class ControlPanel(QWidget):
    """Slider controls for noise reduction parameters"""

    parameters_changed = pyqtSignal(dict)  # Emits dict with current parameters

    def __init__(self):
        super().__init__()
        self.sliders = {}
        self.value_labels = {}
        self.preset_manager = PresetManager()
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

        # Control buttons layout
        button_layout = QHBoxLayout()

        # Reset button
        reset_btn = QPushButton('Reset to Defaults')
        reset_btn.clicked.connect(self._reset_defaults)
        button_layout.addWidget(reset_btn)

        # Preset buttons
        save_preset_btn = QPushButton('Save Preset')
        save_preset_btn.clicked.connect(self._on_save_preset)
        button_layout.addWidget(save_preset_btn)

        load_preset_btn = QPushButton('Load Preset')
        load_preset_btn.clicked.connect(self._on_load_preset)
        button_layout.addWidget(load_preset_btn)

        main_layout.addLayout(button_layout)

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

    def _on_save_preset(self):
        """Handle save preset button"""
        name, ok = QInputDialog.getText(
            self,
            'Save Preset',
            'Enter preset name:',
            text=''
        )

        if not ok or not name.strip():
            return

        try:
            params = self.get_parameters()
            self.preset_manager.save_preset(name, params)
            QMessageBox.information(self, 'Success', f'Preset "{name}" saved!')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save preset: {e}')

    def _on_load_preset(self):
        """Handle load preset button"""
        preset_names = self.preset_manager.get_preset_names()

        if not preset_names:
            QMessageBox.information(self, 'No Presets', 'No presets available')
            return

        dialog = QDialog(self)
        dialog.setWindowTitle('Load Preset')
        dialog.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Select a preset:'))

        list_widget = QListWidget()
        for name in preset_names:
            list_widget.addItem(QListWidgetItem(name))

        layout.addWidget(list_widget)

        button_layout = QHBoxLayout()
        load_btn = QPushButton('Load')
        cancel_btn = QPushButton('Cancel')
        delete_btn = QPushButton('Delete')

        load_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        button_layout.addWidget(load_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        def on_delete():
            """Delete selected preset"""
            current_item = list_widget.currentItem()
            if not current_item:
                QMessageBox.warning(dialog, 'No Selection', 'Please select a preset to delete')
                return
            preset_name = current_item.text()
            reply = QMessageBox.question(
                dialog,
                'Confirm Delete',
                f'Delete preset "{preset_name}"?'
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.preset_manager.delete_preset(preset_name)
                list_widget.takeItem(list_widget.row(current_item))
                QMessageBox.information(dialog, 'Success', f'Preset "{preset_name}" deleted')

        delete_btn.clicked.connect(on_delete)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            current_item = list_widget.currentItem()
            if current_item:
                preset_name = current_item.text()
                try:
                    params = self.preset_manager.load_preset(preset_name)
                    for key, value in params.items():
                        if key in self.sliders:
                            self.sliders[key].setValue(value)
                except Exception as e:
                    QMessageBox.critical(self, 'Error', f'Failed to load preset: {e}')

    def get_parameters(self) -> dict:
        """Get current parameter values"""
        return {
            'threshold': self.sliders['threshold'].value(),
            'reduction': self.sliders['reduction'].value(),
            'freq_smoothing': self.sliders['freq_smoothing'].value(),
            'time_smoothing': self.sliders['time_smoothing'].value(),
        }
