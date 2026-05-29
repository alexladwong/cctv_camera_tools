#!/usr/bin/env python3
"""
HTTP/MJPEG CCTV Stream Viewer
For cameras that only have port 80 open (web interface only)
"""

import sys
import cv2
import numpy as np
import requests
import threading
import time
from datetime import datetime
from urllib.parse import urljoin, urlencode

try:
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import *
    from PyQt6.QtGui import *
except ImportError:
    print("[!] PyQt6 not installed. Run: pip install PyQt6")
    sys.exit(1)


class HTTPCameraViewer(QMainWindow):
    """Viewer for HTTP-based CCTV cameras (MJPEG streams)"""
    
    def __init__(self, device_ip: str, credentials=None):
        super().__init__()
        self.device_ip = device_ip
        self.credentials = credentials or ("", "")
        self.stream_url = None
        self.cap = None
        self.timer = None
        self.recording = False
        self.video_writer = None
        self.frame_counter = 0
        self.init_ui()
        self.discover_stream()
        
    def init_ui(self):
        self.setWindowTitle(f"HTTP Camera Viewer - {self.device_ip}")
        self.setGeometry(200, 200, 900, 700)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Video display
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("background-color: black; border: 2px solid #3c3c3c;")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.video_label)
        
        # Status
        self.status_label = QLabel("Discovering stream URL...")
        self.status_label.setStyleSheet("color: #e5c07b; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Controls
        controls = QHBoxLayout()
        
        self.snapshot_btn = QPushButton("📸 Snapshot")
        self.snapshot_btn.clicked.connect(self.take_snapshot)
        controls.addWidget(self.snapshot_btn)
        
        self.record_btn = QPushButton("🎥 Start Recording")
        self.record_btn.clicked.connect(self.toggle_recording)
        controls.addWidget(self.record_btn)
        
        self.browse_btn = QPushButton("🌐 Open Web Interface")
        self.browse_btn.clicked.connect(self.open_web_interface)
        controls.addWidget(self.browse_btn)
        
        self.diagnose_btn = QPushButton("🔧 Scan Stream Paths")
        self.diagnose_btn.clicked.connect(self.scan_stream_paths)
        controls.addWidget(self.diagnose_btn)
        
        layout.addLayout(controls)
        
        # Manual URL input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Stream URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("http://192.168.1.1/video or http://192.168.1.1/mjpeg")
        url_layout.addWidget(self.url_input)
        
        self.apply_btn = QPushButton("Apply URL")
        self.apply_btn.clicked.connect(self.apply_manual_url)
        url_layout.addWidget(self.apply_btn)
        
        layout.addLayout(url_layout)
        
        # Debug log
        self.debug_text = QTextEdit()
        self.debug_text.setMaximumHeight(150)
        self.debug_text.setReadOnly(True)
        self.debug_text.setStyleSheet("background-color: #1e1e1e; font-family: monospace; font-size: 10px;")
        layout.addWidget(QLabel("Debug Log:"))
        layout.addWidget(self.debug_text)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.debug("HTTP Camera Viewer initialized")
    
    def debug(self, message):
        """Add debug message"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.debug_text.append(f"[{timestamp}] {message}")
        QApplication.processEvents()
    
    def discover_stream(self):
        """Discover MJPEG/HTTP stream URL"""
        self.debug("Searching for HTTP stream endpoints...")
        
        # Common HTTP stream paths for various cameras
        stream_paths = [
            # Generic MJPEG paths
            "/video",
            "/live",
            "/mjpeg",
            "/stream",
            "/cgi-bin/mjpg/video.cgi",
            "/axis-cgi/mjpg/video.cgi",
            "/cgi-bin/video.cgi",
            "/cgi-bin/h264",
            "/cgi-bin/mjpg",
            "/videos",
            "/live/mjpeg",
            "/live/video",
            "/video.cgi",
            "/videostream.cgi",
            "/jpg/image.jpg",
            "/snapshot.jpg",
            "/tmpfs/auto.jpg",
            "/image.jpg",
            "/cgi-bin/snapshot.cgi",
            "/cgi-bin/image.cgi",
            "/cgi-bin/stream.cgi",
            "/api/stream",
            "/api/video",
            "/media",
            "/h264",
            "/h264ESVideoTrack",
            
            # Hikvision specific
            "/ISAPI/Streaming/channels/101/picture",
            "/ISAPI/Streaming/channels/102/httpPreview",
            "/Streaming/Channels/1/httppreview",
            
            # Dahua specific
            "/cgi-bin/mjpg/video.cgi?channel=1&subtype=0",
            "/cgi-bin/snapshot.cgi?channel=1",
            
            # TP-Link specific
            "/stream/get",
            
            # Foscam specific
            "/videoMain",
            
            # Reolink specific
            "/bcs/channel0_main.bcs?channel=0&stream=0",
            
            # Annke specific
            "/cgi-bin/stream.cgi",
        ]
        
        # Try each path
        for path in stream_paths:
            if self.test_http_stream(path):
                self.stream_url = f"http://{self.device_ip}{path}"
                self.debug(f"✅ FOUND WORKING STREAM: {self.stream_url}")
                self.start_stream()
                return
        
        self.debug("❌ No working stream found")
        self.status_label.setText("❌ No stream found - Try manual URL or scan paths")
        self.status_label.setStyleSheet("color: #f48771; padding:        """Test if an HTTP path provides a va            self.debug(fh=auth, timeout=2, verify=False)
                if resp.status_code == 200:
                    content_type = resp.headers.get('Content-Type', '')
                    if 'mjpeg' in content_type or 'multipart' in content_type or 'image' in content_type:
                        self.debug(f"  ✓ Content-Type: {content_type}")
                        return True
            except:
                pass
            
            # Try to actually read a frame with OpenCV
            if auth:
                auth_url = f"http://{self.credentials[0]}:{self.credentials[1]}@{self.device_ip}{path}"
                cap = cv2.VideoCapture(auth_url, cv2.CAP_FFMPEG)
            else:
                cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    self.debug(f"  ✓ SUCCESS - Stream works!")
                    return True
            
            return False
            
        except Exception as e:
            self.debug(f"  ✗ Error: {str(e)[:50]}")
            return False
    
    def scan_stream_paths(self):
        """Interactive scan of common paths"""
        self.debug("\n" + "=" * 50)
        self.debug("SCANNING ALL POSSIBLE STREAM PATHS")
        
        paths_to_try = [
            "/video", "/live", "/mjpeg", "/stream", "/cgi-bin/mjpg/video.cgi",
            "/axis-cgi/mjpg/video.cgi", "/cgi-bin/video.cgi", "/videostream.cgi",
            "/cgi-bin/snapshot.cgi", "/snapshot.jpg", "/image.jpg", "/cgi-bin/image.cgi",
            "/ISAPI/Streaming/channels/101/picture", "/Streaming/Channels/1/httppreview",
            "/cgi-bin/mjpg/video.cgi?channel=1&subtype=0", "/bcs/channel0_main.bcs?channel=0&stream=0",
            "/tmpfs/auto.jpg", "/jpg/image.jpg", "/cgi-bin/stream.cgi", "/api/stream"
        ]
        
        working_paths = []
        
        for path in paths_to_try:
            if self.test_http_stream(path):
                working_paths.append(path)
                self.debug(f"✅ WORKING: {path}")
            time.sleep(0.2)  # Rate limit
        
        self.debug("=" * 50)
        
        if working_paths:
            msg = f"Found {len(working_paths)} working streams:\n\n"
            for path in working_paths[:5]:
                msg += f"• http://{self.device_ip}{path}\n"
            msg += "\nCopy a URL and click 'Apply URL'"
            QMessageBox.information(self, "Scan Results", msg)
        else:
            QMessageBox.warning(self, "Scan Results", 
                               "No working streams found.\n\n"
                               "Try:\n"
                               "1. Check if camera requires authentication\n"
                               "2. Try entering URL manually\n"
                               "3. Open web interface to find stream URL")
    
    def start_stream(self):
        """Start the HTTP stream"""
        if not self.stream_url:
            return
        
        try:
            self.debug(f"Starting stream: {self.stream_url}")
            self.cap = cv2.VideoCapture(self.stream_url, cv2.CAP_FFMPEG)
            
            if self.cap.isOpened():
                self.status_label.setText(f"✅ Streaming from {self.device_ip}")
                self.status_label.setStyleSheet("color: #4ec9b0; padding: 5px;")
                
                self.timer = QTimer()
                self.timer.timeout.connect(self.update_frame)
                self.timer.start(33)
                
                self.debug("Stream started successfully")
                self.status_bar.showMessage("Connected to camera")
            else:
                self.debug("Failed to open video capture")
                
        except Exception as e:
            self.debug(f"Error starting stream: {e}")
    
    def update_frame(self):
        """Update video frame"""
        if self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None and frame.size > 0:
                    self.frame_counter += 1
                    
                    # Resize if needed
                    if frame.shape[1] > 800:
                        scale = 800 / frame.shape[1]
                        new_width = int(frame.shape[1] * scale)
                        new_height = int(frame.shape[0] * scale)
                        frame = cv2.resize(frame, (new_width, new_height))
                    
                    # Convert to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = frame_rgb.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(qt_image)
                    
                    scaled_pixmap = pixmap.scaled(
                        self.video_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.video_label.setPixmap(scaled_pixmap)
                    
                    # Recording
                    if self.recording and self.video_writer:
                        self.video_writer.write(frame)
                    
                    # Update status every 100 frames
                    if self.frame_counter % 100 == 0:
                        self.status_bar.showMessage(f"Frames: {self.frame_counter}")
                        
            except Exception as e:
                self.debug(f"Frame error: {e}")
    
    def apply_manual_url(self):
        """Apply manually entered URL"""
        manual_url = self.url_input.text().strip()
        if not manual_url:
            return
        
        if not manual_url.startswith('http://'):
            manual_url = f"http://{manual_url}"
        
        self.debug(f"Applying manual URL: {manual_url}")
        self.stream_url = manual_url
        
        if self.timer:
            self.timer.stop()
        if self.cap:
            self.cap.release()
        
        self.start_stream()
    
    def open_web_interface(self):
        """Open camera's web interface in browser"""
        import webbrowser
        url = f"http://{self.device_ip}"
        webbrowser.open(url)
        self.debug(f"Opened web interface: {url}")
    
    def take_snapshot(self):
        """Capture snapshot"""
        if self.video_label.pixmap():
            filename = f"snapshot_{self.device_ip}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.video_label.pixmap().save(filename)
            self.status_bar.showMessage(f"Snapshot saved: {filename}")
            self.debug(f"Snapshot: {filename}")
    
    def toggle_recording(self):
        """Toggle recording"""
        if not self.recording:
            filename = f"recording_{self.device_ip}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(filename, fourcc, 15.0, (640, 480))
            self.recording = True
            self.record_btn.setText("⏹️ Stop Recording")
            self.status_bar.showMessage(f"Recording: {filename}")
            self.debug(f"Started recording: {filename}")
        else:
            self.recording = False
            if self.video_writer:
                self.video_writer.release()
            self.record_btn.setText("🎥 Start Recording")
            self.status_bar.showMessage("Recording stopped")
            self.debug("Recording stopped")
    
    def closeEvent(self, event):
        """Cleanup"""
        if self.timer:
            self.timer.stop()
        if self.cap:
            self.cap.release()
        if self.recording and self.video_writer:
            self.video_writer.release()
        event.accept()


# Alternative: Simple screenshot-based viewer (works with any HTTP camera)
class ScreenshotBasedViewer(QMainWindow):
    """For cameras that only provide snapshots, not continuous stream"""
    
    def __init__(self, device_ip: str, credentials=None):
        super().__init__()
        self.device_ip = device_ip
        self.credentials = credentials
        self.timer = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(f"Snapshot Viewer - {self.device_ip}")
        self.setGeometry(200, 200, 800, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        self.image_label = QLabel()
        self.image_label.setMinimumSize(640, 480)
        self.image_label.setStyleSheet("background-color: black;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)
        
        self.status_label = QLabel("Fetching snapshots...")
        layout.addWidget(self.status_label)
        
        # Controls
        controls = QHBoxLayout()
        
        self.fps_input = QLineEdit("1")
        self.fps_input.setMaximumWidth(50)
        controls.addWidget(QLabel("FPS:"))
        controls.addWidget(self.fps_input)
        
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.clicked.connect(self.start_capture)
        controls.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_capture)
        self.stop_btn.setEnabled(False)
        controls.addWidget(self.stop_btn)
        
        layout.addLayout(controls)
        
        self.setCentralWidget(central)
    
    def get_snapshot(self):
        """Fetch a snapshot from the camera"""
        snapshot_urls = [
            f"http://{self.device_ip}/snapshot.jpg",
            f"http://{self.device_ip}/image.jpg",
            f"http://{self.device_ip}/cgi-bin/snapshot.cgi",
            f"http://{self.device_ip}/cgi-bin/image.cgi",
            f"http://{self.device_ip}/jpg/image.jpg",
            f"http://{self.device_ip}/tmpfs/auto.jpg",
        ]
        
        for url in snapshot_urls:
            try:
                auth = None
                if self.credentials and self.credentials[0]:
                    auth = (self.credentials[0], self.credentials[1])
                
                response = requests.get(url, auth=auth, timeout=2, verify=False)
                if response.status_code == 200 and b'\xff\xd8' in response.content[:10]:
                    # It's a JPEG
                    img_array = np.frombuffer(response.content, np.uint8)
                    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    if img is not None:
                        return img
            except:
                pass
        
        return None
    
    def update_frame(self):
        """Fetch and display snapshot"""
        img = self.get_snapshot()
        if img is not None:
            # Convert to RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = img_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            scaled = pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
            self.status_label.setText(f"Last frame: {datetime.now().strftime('%H:%M:%S')}")
    
    def start_capture(self):
        """Start periodic snapshot capture"""
        fps = float(self.fps_input.text()) if self.fps_input.text() else 1
        interval = int(1000 / fps)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(interval)
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText(f"Capturing at {fps} FPS")
    
    def stop_capture(self):
        """Stop capture"""
        if self.timer:
            self.timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Stopped")
    
    def closeEvent(self, event):
        self.stop_capture()
        event.accept()


# Main launcher
def main():
    app = QApplication(sys.argv)
    
    # Get camera IP
    ip, ok = QInputDialog.getText(None, "Camera IP", 
                                   "Enter camera IP address:",
                                   text="192.168.1.1")
    
    if not ok or not ip:
        print("No IP entered")
        sys.exit(1)
    
    # Ask for stream type
    stream_type, ok = QInputDialog.getItem(None, "Stream Type",
                                           "Select stream type:",
                                           ["HTTP/MJPEG Stream", "Snapshot (Slower)"],
                                           0, False)
    
    if stream_type == "HTTP/MJPEG Stream":
        viewer = HTTPCameraViewer(ip)
    else:
        viewer = ScreenshotBasedViewer(ip)
    
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

