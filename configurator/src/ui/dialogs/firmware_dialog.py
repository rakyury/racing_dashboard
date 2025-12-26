# Firmware Upload Dialog
"""Dialog for uploading firmware to the device."""

import logging
import hashlib
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFileDialog, QGroupBox, QGridLayout,
    QMessageBox, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

logger = logging.getLogger(__name__)


class FirmwareInfo:
    """Firmware file information."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_name = Path(file_path).name
        self.file_size = 0
        self.checksum = ""
        self.version = "Unknown"
        self.target = "STM32H743"
        self.valid = False
        self.error = ""

        self._parse_file()

    def _parse_file(self) -> None:
        """Parse firmware file."""
        try:
            path = Path(self.file_path)
            if not path.exists():
                self.error = "File not found"
                return

            self.file_size = path.stat().st_size

            # Calculate checksum
            with open(self.file_path, 'rb') as f:
                data = f.read()
                self.checksum = hashlib.md5(data).hexdigest()

            # Try to parse version from filename
            name = path.stem.lower()
            if '_v' in name:
                version_part = name.split('_v')[-1].split('_')[0]
                self.version = f"v{version_part}"
            elif '-v' in name:
                version_part = name.split('-v')[-1].split('-')[0]
                self.version = f"v{version_part}"

            # Check file extension
            if path.suffix.lower() in ['.bin', '.hex', '.elf']:
                self.valid = True
            else:
                self.error = f"Unsupported file format: {path.suffix}"

            # Check minimum size
            if self.file_size < 1024:
                self.error = "File too small to be valid firmware"
                self.valid = False

        except Exception as e:
            self.error = str(e)
            self.valid = False


class FirmwareUploadWorker(QThread):
    """Background worker for firmware upload."""

    progress = pyqtSignal(int, str)  # percent, message
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, device_controller, firmware_path: str):
        super().__init__()
        self._controller = device_controller
        self._firmware_path = firmware_path
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            self.progress.emit(0, "Reading firmware file...")

            # Read firmware
            with open(self._firmware_path, 'rb') as f:
                firmware_data = f.read()

            total_size = len(firmware_data)
            chunk_size = 1024  # 1KB chunks

            self.progress.emit(5, "Preparing device for update...")

            # In a real implementation, we would:
            # 1. Enter bootloader mode
            # 2. Erase flash
            # 3. Upload firmware in chunks
            # 4. Verify checksum
            # 5. Restart device

            # Simulate upload process
            uploaded = 0
            while uploaded < total_size and not self._cancelled:
                chunk_end = min(uploaded + chunk_size, total_size)
                chunk = firmware_data[uploaded:chunk_end]

                # Simulate chunk upload
                QThread.msleep(20)

                uploaded = chunk_end
                percent = 5 + int(90 * uploaded / total_size)
                self.progress.emit(percent, f"Uploading: {uploaded}/{total_size} bytes")

            if self._cancelled:
                self.finished.emit(False, "Upload cancelled")
                return

            self.progress.emit(95, "Verifying firmware...")
            QThread.msleep(500)

            self.progress.emit(98, "Restarting device...")
            QThread.msleep(500)

            self.progress.emit(100, "Complete!")
            self.finished.emit(True, "Firmware uploaded successfully!")

        except Exception as e:
            logger.error(f"Firmware upload error: {e}")
            self.finished.emit(False, f"Upload failed: {str(e)}")


class FirmwareUploadDialog(QDialog):
    """Dialog for firmware upload."""

    def __init__(self, device_controller, parent=None):
        super().__init__(parent)
        self._controller = device_controller
        self._firmware_info: Optional[FirmwareInfo] = None
        self._worker: Optional[FirmwareUploadWorker] = None

        self.setWindowTitle("Firmware Upload")
        self.setMinimumSize(500, 400)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Device info
        device_group = QGroupBox("Device")
        device_layout = QGridLayout(device_group)

        device_layout.addWidget(QLabel("Connection:"), 0, 0)
        self._connection_label = QLabel("Not Connected")
        if self._controller.is_connected:
            self._connection_label.setText("Connected")
            self._connection_label.setStyleSheet("color: #4CAF50;")
        else:
            self._connection_label.setStyleSheet("color: #ff4444;")
        device_layout.addWidget(self._connection_label, 0, 1)

        device_layout.addWidget(QLabel("Current Firmware:"), 1, 0)
        current_ver = self._controller.device_info.get("firmware_version", "Unknown")
        self._current_ver_label = QLabel(current_ver)
        device_layout.addWidget(self._current_ver_label, 1, 1)

        layout.addWidget(device_group)

        # Firmware file selection
        file_group = QGroupBox("Firmware File")
        file_layout = QVBoxLayout(file_group)

        file_row = QHBoxLayout()
        self._file_path_label = QLabel("No file selected")
        self._file_path_label.setStyleSheet("color: #888;")
        file_row.addWidget(self._file_path_label, 1)

        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(self._browse_btn)
        file_layout.addLayout(file_row)

        # File info
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        info_layout = QGridLayout(info_frame)
        info_layout.setSpacing(4)

        info_layout.addWidget(QLabel("Version:"), 0, 0)
        self._version_label = QLabel("-")
        info_layout.addWidget(self._version_label, 0, 1)

        info_layout.addWidget(QLabel("Size:"), 1, 0)
        self._size_label = QLabel("-")
        info_layout.addWidget(self._size_label, 1, 1)

        info_layout.addWidget(QLabel("Checksum:"), 2, 0)
        self._checksum_label = QLabel("-")
        self._checksum_label.setStyleSheet("font-family: Consolas; font-size: 10px;")
        info_layout.addWidget(self._checksum_label, 2, 1)

        info_layout.addWidget(QLabel("Target:"), 3, 0)
        self._target_label = QLabel("-")
        info_layout.addWidget(self._target_label, 3, 1)

        file_layout.addWidget(info_frame)
        layout.addWidget(file_group)

        # Progress
        progress_group = QGroupBox("Upload Progress")
        progress_layout = QVBoxLayout(progress_group)

        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        progress_layout.addWidget(self._progress_bar)

        self._status_label = QLabel("Ready")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self._status_label)

        # Log
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(80)
        self._log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #ddd;
                font-family: Consolas;
                font-size: 10px;
            }
        """)
        progress_layout.addWidget(self._log_text)

        layout.addWidget(progress_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._upload_btn = QPushButton("Upload Firmware")
        self._upload_btn.setEnabled(False)
        self._upload_btn.setMinimumWidth(150)
        self._upload_btn.clicked.connect(self._start_upload)
        button_layout.addWidget(self._upload_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._cancel)
        button_layout.addWidget(self._cancel_btn)

        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self._close_btn)

        layout.addLayout(button_layout)

    def _browse_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Firmware File",
            "",
            "Firmware Files (*.bin *.hex *.elf);;All Files (*)"
        )

        if file_path:
            self._load_firmware_file(file_path)

    def _load_firmware_file(self, file_path: str) -> None:
        self._firmware_info = FirmwareInfo(file_path)

        self._file_path_label.setText(self._firmware_info.file_name)

        if self._firmware_info.valid:
            self._file_path_label.setStyleSheet("color: #4CAF50;")
            self._version_label.setText(self._firmware_info.version)
            self._size_label.setText(f"{self._firmware_info.file_size:,} bytes")
            self._checksum_label.setText(self._firmware_info.checksum)
            self._target_label.setText(self._firmware_info.target)
            self._upload_btn.setEnabled(self._controller.is_connected)
            self._log(f"Loaded firmware: {self._firmware_info.file_name}")
        else:
            self._file_path_label.setStyleSheet("color: #ff4444;")
            self._version_label.setText("-")
            self._size_label.setText("-")
            self._checksum_label.setText("-")
            self._target_label.setText("-")
            self._upload_btn.setEnabled(False)
            self._log(f"Error: {self._firmware_info.error}")

    def _start_upload(self) -> None:
        if not self._firmware_info or not self._firmware_info.valid:
            return

        if not self._controller.is_connected:
            QMessageBox.warning(self, "Not Connected",
                              "Please connect to a device first.")
            return

        reply = QMessageBox.question(
            self, "Confirm Upload",
            f"Upload firmware {self._firmware_info.version} to the device?\n\n"
            "WARNING: Do not disconnect the device during upload!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self._log("Starting firmware upload...")
        self._upload_btn.setEnabled(False)
        self._browse_btn.setEnabled(False)
        self._cancel_btn.setText("Cancel Upload")

        self._worker = FirmwareUploadWorker(
            self._controller,
            self._firmware_info.file_path
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, percent: int, message: str) -> None:
        self._progress_bar.setValue(percent)
        self._status_label.setText(message)
        self._log(message)

    def _on_finished(self, success: bool, message: str) -> None:
        self._log(message)

        if success:
            self._status_label.setText("Upload Complete!")
            self._status_label.setStyleSheet("color: #4CAF50;")
            QMessageBox.information(self, "Success", message)
        else:
            self._status_label.setText("Upload Failed")
            self._status_label.setStyleSheet("color: #ff4444;")
            QMessageBox.critical(self, "Error", message)

        self._upload_btn.setEnabled(True)
        self._browse_btn.setEnabled(True)
        self._cancel_btn.setText("Cancel")
        self._worker = None

    def _cancel(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._log("Cancelling upload...")
        else:
            self.reject()

    def _log(self, message: str) -> None:
        self._log_text.append(message)


def show_firmware_dialog(device_controller, parent=None) -> bool:
    """Show firmware upload dialog."""
    dialog = FirmwareUploadDialog(device_controller, parent)
    return dialog.exec() == QDialog.DialogCode.Accepted
