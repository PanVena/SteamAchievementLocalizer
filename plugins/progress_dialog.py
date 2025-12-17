"""
Progress Dialog Plugin for Steam Achievement Localizer
Provides progress dialog with threading support for long-running operations
"""
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QProgressDialog


class WorkerThread(QThread):
    """Worker thread for background operations"""
    progress = pyqtSignal(int, str)  # (progress_value, status_message)
    finished = pyqtSignal(object)  # result
    error = pyqtSignal(str)  # error message
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._is_cancelled = False
    
    def run(self):
        """Execute the function in background thread"""
        try:
            # Add progress callback to kwargs
            self.kwargs['progress_callback'] = self.progress.emit
            self.kwargs['is_cancelled'] = lambda: self._is_cancelled
            
            result = self.func(*self.args, **self.kwargs)
            
            if not self._is_cancelled:
                self.finished.emit(result)
        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(str(e))
    
    def cancel(self):
        """Cancel the operation"""
        self._is_cancelled = True


class ProgressDialog(QProgressDialog):
    """Progress dialog with thread support"""
    
    def __init__(self, parent, title, label_text, maximum=100):
        super().__init__(label_text, "Cancel", 0, maximum, parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumDuration(0)
        self.setAutoClose(True)
        self.setAutoReset(True)
        self.worker = None
        self.result_callback = None
        self.error_callback = None
    
    def run_task(self, func, *args, **kwargs):
        """Run a task in background thread"""
        self.worker = WorkerThread(func, *args, **kwargs)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.canceled.connect(self.on_canceled)
        self.worker.start()
    
    def update_progress(self, value, message):
        """Update progress bar value and message"""
        self.setValue(value)
        self.setLabelText(message)
        # Process events to keep UI responsive
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
    
    def on_finished(self, result):
        """Handle task completion"""
        self.setValue(self.maximum())
        if self.result_callback:
            self.result_callback(result)
        self.accept()
    
    def on_error(self, error_msg):
        """Handle task error"""
        self.cancel()
        if self.error_callback:
            self.error_callback(error_msg)
        self.reject()
    
    def on_canceled(self):
        """Handle user cancellation"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(1000)  # Wait up to 1 second
            if self.worker.isRunning():
                self.worker.terminate()
                self.worker.wait()
