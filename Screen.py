import sys
import os
import pyautogui
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QWidget, QFileDialog, QComboBox,
                            QSpinBox, QCheckBox, QMessageBox)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon, QPixmap, QImage

class ScreenRecorderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screen Recorder Pro")
        self.setWindowIcon(QIcon("icon.png"))  # Add your own icon file
        self.setGeometry(100, 100, 600, 400)
        
        # Recording variables
        self.recording = False
        self.out = None
        self.timer = QTimer()
        self.frame_count = 0
        
        # UI Setup
        self.init_ui()
        
    def init_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout()
        
        # Preview area
        self.preview_label = QLabel("Preview will appear here")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("border: 2px solid gray; background-color: black;")
        layout.addWidget(self.preview_label, 1)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Record button
        self.record_btn = QPushButton("Start Recording")
        self.record_btn.setStyleSheet("background-color: #ff4444; color: white;")
        self.record_btn.clicked.connect(self.toggle_recording)
        controls_layout.addWidget(self.record_btn)
        
        # Stop button
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_recording)
        controls_layout.addWidget(self.stop_btn)
        
        layout.addLayout(controls_layout)
        
        # Settings
        settings_layout = QVBoxLayout()
        
        # Resolution
        res_layout = QHBoxLayout()
        res_layout.addWidget(QLabel("Resolution:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(640, 3840)
        self.width_spin.setValue(1440)
        res_layout.addWidget(self.width_spin)
        res_layout.addWidget(QLabel("x"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(480, 2160)
        self.height_spin.setValue(900)
        res_layout.addWidget(self.height_spin)
        settings_layout.addLayout(res_layout)
        
        # FPS
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("FPS:"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(30)
        fps_layout.addWidget(self.fps_spin)
        settings_layout.addLayout(fps_layout)
        
        # Codec
        codec_layout = QHBoxLayout()
        codec_layout.addWidget(QLabel("Codec:"))
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["XVID (AVI)", "MP4V (MP4)", "MJPG (MJPEG)"])
        codec_layout.addWidget(self.codec_combo)
        settings_layout.addLayout(codec_layout)
        
        # Output file
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Output File:"))
        self.file_path = QLabel("Recording.avi")
        file_layout.addWidget(self.file_path)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        settings_layout.addLayout(file_layout)
        
        # Options
        self.show_preview = QCheckBox("Show preview while recording")
        self.show_preview.setChecked(True)
        settings_layout.addWidget(self.show_preview)
        
        layout.addLayout(settings_layout)
        
        # Status bar
        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet("color: gray;")
        layout.addWidget(self.status_bar)
        
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        
        # Timer for preview
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        self.preview_timer.start(100)  # 10 FPS preview
        
    def browse_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Recording", "Recording.avi", 
            "Video Files (*.avi *.mp4 *.mov);;All Files (*)", 
            options=options)
        
        if file_name:
            self.file_path.setText(file_name)
    
    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.pause_recording()
    
    def start_recording(self):
        # Get settings
        resolution = (self.width_spin.value(), self.height_spin.value())
        fps = self.fps_spin.value()
        filename = self.file_path.text()
        
        # Determine codec
        codec_choice = self.codec_combo.currentText()
        if "XVID" in codec_choice:
            codec = cv2.VideoWriter_fourcc(*"XVID")
            if not filename.endswith('.avi'):
                filename += '.avi'
        elif "MP4V" in codec_choice:
            codec = cv2.VideoWriter_fourcc(*"mp4v")
            if not filename.endswith('.mp4'):
                filename += '.mp4'
        else:  # MJPG
            codec = cv2.VideoWriter_fourcc(*"MJPG")
            if not filename.endswith('.avi'):
                filename += '.avi'
        
        try:
            self.out = cv2.VideoWriter(filename, codec, fps, resolution)
            self.recording = True
            self.frame_count = 0
            
            self.record_btn.setText("Pause")
            self.record_btn.setStyleSheet("background-color: #ffaa00; color: white;")
            self.stop_btn.setEnabled(True)
            
            self.status_bar.setText(f"Recording to {filename}...")
            self.status_bar.setStyleSheet("color: green;")
            
            # Start recording timer
            self.timer.timeout.connect(self.record_frame)
            self.timer.start(1000 // fps)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not start recording:\n{str(e)}")
    
    def pause_recording(self):
        self.recording = False
        self.timer.stop()
        
        self.record_btn.setText("Resume")
        self.record_btn.setStyleSheet("background-color: #44aa44; color: white;")
        
        self.status_bar.setText(f"Recording paused - {self.frame_count} frames captured")
        self.status_bar.setStyleSheet("color: orange;")
    
    def stop_recording(self):
        if self.out:
            self.recording = False
            self.timer.stop()
            self.out.release()
            self.out = None
            
            self.record_btn.setText("Start Recording")
            self.record_btn.setStyleSheet("background-color: #ff4444; color: white;")
            self.stop_btn.setEnabled(False)
            
            self.status_bar.setText(f"Recording saved - {self.frame_count} frames captured")
            self.status_bar.setStyleSheet("color: blue;")
            
            QMessageBox.information(self, "Success", "Recording saved successfully!")
    
    def record_frame(self):
        if self.recording and self.out:
            try:
                img = pyautogui.screenshot()
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Resize to selected resolution
                frame = cv2.resize(frame, (self.width_spin.value(), self.height_spin.value()))
                
                self.out.write(frame)
                self.frame_count += 1
                
                if self.show_preview.isChecked():
                    self.update_preview(frame)
                
            except Exception as e:
                self.status_bar.setText(f"Error: {str(e)}")
                self.status_bar.setStyleSheet("color: red;")
                self.stop_recording()
    
    def update_preview(self, frame=None):
        if frame is None:
            # Just show current screen
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Resize for preview
        preview = cv2.resize(frame, (640, 360))
        
        # Convert to QImage
        height, width, channel = preview.shape
        bytes_per_line = 3 * width
        q_img = QImage(preview.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        
        # Display
        self.preview_label.setPixmap(QPixmap.fromImage(q_img))
    
    def closeEvent(self, event):
        if self.recording:
            reply = QMessageBox.question(
                self, 'Recording in Progress',
                "A recording is in progress. Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.stop_recording()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = ScreenRecorderApp()
    window.show()
    
    sys.exit(app.exec_())