"""Main application window"""

import os
import numpy as np
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QFileDialog, QMessageBox, QProgressBar,
                             QPushButton, QTabWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from .control_panel import ControlPanel
from .preview_controls import PreviewControls
from ..core import AudioProcessor
from ..workers.processing_worker import ProcessingWorker
from ..utils.validators import format_duration, is_valid_audio_file
from ..utils.config import (WINDOW_WIDTH, WINDOW_HEIGHT,
                            get_supported_input_formats, get_supported_output_formats,
                            get_format_from_extension)


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Noise Removal Tool')
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)

        self.processor = AudioProcessor()
        self.processing_worker = None
        self.processed_audio = None

        self._setup_ui()
        self._setup_menu()

    def _setup_ui(self):
        """Create main UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        # File info display
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("File:"))
        self.file_label = QLabel("No file loaded")
        self.file_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.file_label)

        info_layout.addWidget(QLabel("SR:"))
        self.sr_label = QLabel("-")
        info_layout.addWidget(self.sr_label)

        info_layout.addWidget(QLabel("Duration:"))
        self.duration_label = QLabel("-")
        info_layout.addWidget(self.duration_label)

        info_layout.addStretch()
        main_layout.addLayout(info_layout)

        # Create tabs for controls and preview
        tabs = QTabWidget()

        # Control tab
        control_tab = QWidget()
        control_layout = QVBoxLayout()
        self.control_panel = ControlPanel()
        self.control_panel.parameters_changed.connect(self._on_parameters_changed)
        control_layout.addWidget(self.control_panel)
        control_tab.setLayout(control_layout)
        tabs.addTab(control_tab, "Parameters")

        # Preview tab
        preview_tab = QWidget()
        preview_layout = QVBoxLayout()
        self.preview_controls = PreviewControls()
        self.preview_controls.request_preview.connect(self._on_preview_requested)
        preview_layout.addWidget(self.preview_controls)
        preview_tab.setLayout(preview_layout)
        tabs.addTab(preview_tab, "Preview")

        main_layout.addWidget(tabs)

        # Processing controls
        process_layout = QHBoxLayout()
        self.process_btn = QPushButton('Process Full File')
        self.process_btn.clicked.connect(self._on_process_clicked)
        self.process_btn.setEnabled(False)
        process_layout.addWidget(self.process_btn)

        self.save_btn = QPushButton('Save Processed Audio')
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.save_btn.setEnabled(False)
        process_layout.addWidget(self.save_btn)

        main_layout.addLayout(process_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Status bar
        self.statusBar().showMessage("Ready")

        central_widget.setLayout(main_layout)

    def _setup_menu(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        open_action = file_menu.addAction('Open...')
        open_action.triggered.connect(self._on_open_file)

        file_menu.addSeparator()

        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)

        # Help menu
        help_menu = menubar.addMenu('Help')
        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self._on_about)

    def _build_open_filter(self) -> str:
        """Build dynamic file filter for open dialog"""
        formats = get_supported_input_formats()
        format_patterns = ' '.join(f'*{fmt}' for fmt in formats)
        return f'Audio Files ({format_patterns});;All Files (*)'

    def _build_save_filters(self) -> tuple:
        """Build dynamic file filters for save dialog.

        Returns:
            Tuple of (filter_string, format_map) where format_map maps
            filter descriptions to soundfile format codes
        """
        output_formats = get_supported_output_formats()

        # Sort formats alphabetically by extension
        sorted_formats = sorted(output_formats.items())

        filters = []
        format_map = {}

        for ext, format_code in sorted_formats:
            # Create human-readable format name from extension
            format_name = ext.upper().lstrip('.')
            filter_desc = f'{format_name} Files (*{ext})'
            filters.append(filter_desc)
            format_map[filter_desc] = format_code

        # Add "All Files" option
        filters.append('All Files (*.*)')

        filter_string = ';;'.join(filters)
        return filter_string, format_map

    def _on_open_file(self):
        """Handle file open"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Open Audio File',
            '',
            self._build_open_filter()
        )

        if not file_path:
            return

        if not is_valid_audio_file(file_path):
            QMessageBox.warning(self, 'Invalid File', 'Please select a valid audio file')
            return

        # Load file
        if not self.processor.load_file(file_path):
            QMessageBox.critical(self, 'Error', 'Failed to load audio file')
            return

        # Update UI
        info = self.processor.get_file_info()
        self.file_label.setText(Path(file_path).name)
        self.sr_label.setText(f"{info['sample_rate']} Hz")
        self.duration_label.setText(format_duration(info['duration']))

        # Update max duration for preview
        max_duration = int(info['duration'])
        self.preview_controls.duration_spinbox.setMaximum(max_duration)

        # Enable controls
        self.process_btn.setEnabled(True)
        self.preview_controls.set_full_audio_loaded(True)
        self.preview_controls.set_sample_rate(info['sample_rate'])

        self.statusBar().showMessage(f"Loaded: {Path(file_path).name}")

    def _on_parameters_changed(self, params: dict):
        """Handle parameter changes"""
        # Parameters are now current, can use for preview
        pass

    def _on_preview_requested(self, preview_info: dict):
        """Handle preview request"""
        try:
            params = self.control_panel.get_parameters()
            original, processed = self.processor.generate_preview(
                preview_info['start_sec'],
                preview_info['duration_sec'],
                params
            )

            self.preview_controls.set_preview_data(original, processed)

            # Play original or processed based on request
            if preview_info.get('play_original', False):
                self.preview_controls.play_processed_segment(original)
                self.statusBar().showMessage("Playing original audio")
            else:
                self.preview_controls.play_processed_segment(processed)
                self.statusBar().showMessage("Playing processed audio")

        except Exception as e:
            QMessageBox.critical(self, 'Preview Error', str(e))

    def _on_process_clicked(self):
        """Handle full file processing"""
        params = self.control_panel.get_parameters()

        # Start processing worker
        self.processing_worker = ProcessingWorker(self.processor, params)
        self.processing_worker.progress.connect(self._on_processing_progress)
        self.processing_worker.finished.connect(self._on_processing_finished)
        self.processing_worker.error.connect(self._on_processing_error)

        self.process_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("Processing...")

        self.processing_worker.start()

    def _on_processing_progress(self, percent: int):
        """Update progress bar"""
        self.progress_bar.setValue(percent)

    def _on_processing_finished(self, processed_audio: np.ndarray):
        """Handle processing completion"""
        self.processed_audio = processed_audio
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.statusBar().showMessage("Processing complete! Ready to save.")
        QMessageBox.information(self, 'Success', 'Processing complete!')

    def _on_processing_error(self, error_msg: str):
        """Handle processing error"""
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        self.statusBar().showMessage("Error during processing")
        QMessageBox.critical(self, 'Processing Error', error_msg)

    def _on_save_clicked(self):
        """Handle save processed audio"""
        if self.processed_audio is None:
            QMessageBox.warning(self, 'No Audio', 'No processed audio to save')
            return

        filter_string, format_map = self._build_save_filters()

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            'Save Processed Audio',
            '',
            filter_string
        )

        if not file_path:
            return

        # Determine format from selected filter or file extension
        format_code = None
        if selected_filter in format_map:
            format_code = format_map[selected_filter]

        # Extract extension from file path
        file_ext = '.' + file_path.rsplit('.', 1)[-1].lower() if '.' in file_path else ''

        # If no format selected but extension is valid, use extension
        if format_code is None and file_ext:
            output_formats = get_supported_output_formats()
            format_code = output_formats.get(file_ext)

        # Ensure file has extension based on format
        if format_code is None:
            # Default to WAV if format couldn't be determined
            format_code = 'WAV'
            if not file_path.lower().endswith('.wav'):
                file_path += '.wav'
        else:
            # Add extension if not present
            supported = get_supported_output_formats()
            # Find the extension for this format code
            target_ext = None
            for ext, code in supported.items():
                if code == format_code:
                    target_ext = ext
                    break

            if target_ext and not file_path.lower().endswith(target_ext):
                file_path += target_ext

        try:
            self.processor.save_processed_audio(file_path, self.processed_audio, format_code)
            self.statusBar().showMessage(f"Saved: {Path(file_path).name}")
            QMessageBox.information(self, 'Success', f'Saved to:\n{file_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Save Error', str(e))

    def _on_about(self):
        """Show about dialog"""
        QMessageBox.information(
            self,
            'About Noise Removal Tool',
            'Professional noise removal for audio files\n\n'
            'Version 1.0\n\n'
            'Uses spectral gating with automatic noise profiling'
        )

    def closeEvent(self, event):
        """Handle window close"""
        if self.processing_worker is not None and self.processing_worker.isRunning():
            reply = QMessageBox.question(
                self, 'Processing in Progress',
                'Processing is in progress. Are you sure you want to exit?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

            self.processing_worker.stop()
            self.processing_worker.wait()

        event.accept()
