"""Background processing worker thread"""

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from ..core import AudioProcessor


class ProcessingWorker(QThread):
    """Background worker for audio processing"""

    progress = pyqtSignal(int)           # Progress 0-100%
    finished = pyqtSignal(np.ndarray)    # Processed audio
    error = pyqtSignal(str)              # Error message

    def __init__(self, processor: AudioProcessor, params: dict):
        super().__init__()
        self.processor = processor
        self.params = params
        self._stop_flag = False

    def run(self):
        """Process audio in background"""
        try:
            def progress_callback(percent):
                if not self._stop_flag:
                    self.progress.emit(percent)

            processed = self.processor.process_full_file(
                self.params, progress_callback
            )

            if not self._stop_flag:
                self.finished.emit(processed)

        except Exception as e:
            self.error.emit(f"Processing error: {str(e)}")

    def stop(self):
        """Request stop"""
        self._stop_flag = True
