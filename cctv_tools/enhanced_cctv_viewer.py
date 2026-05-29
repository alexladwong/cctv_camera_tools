#!/usr/bin/env python3
"""
Enhanced HTTP/MJPEG CCTV Stream Viewer - Professional Edition
Features: Multi-auth support, Brand detection, Async streaming, Performance optimized
"""

import sys
import cv2
import numpy as np
import requests
import threading
import time
import queue
from datetime import datetime
from urllib.parse import urljoin, urlencode
from collections import OrderedDict
import hashlib
import base64

try:
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import *
    from PyQt6.QtGui import *
    from PyQt6.QtMultimedia import *
except ImportError:
    print("[!] PyQt6 not installed. Run: pip install PyQt6")
    sys.exit(1)

# Suppress SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CameraDatabase:
    """Database of known camera brands and their configurations"""
    
    BRANDS = {
        "Hikvision": {
            "patterns": ["hikvision", "hik", "ds-2", "iDS-2"],
            "streams": [
                "/ISAPI/Streaming/channels/101/httpPreview",
                "/ISAPI/Streaming/channels/102/httpPreview",
                "/Streaming/Channels/1/httppreview",
                "/cgi-bin/mjpg/video.cgi",
                "/cgi-bin/snapshot.cgi?channel=1",
            ],
            "snapshots": [
                "/ISAPI/Streaming/channels/101/picture",
                "/cgi-bin/snapshot.cgi",
            ],
            "auth_type": "digest",
            "default_creds": [("admin", "12345"), ("admin", "hik12345"), ("admin", "123456789")]
        },
        "Dahua": {
            "patterns": ["dahua", "dh-", "ipc-", "leo"],
            "streams": [
                "/cgi-bin/mjpg/video.cgi?channel=1&subtype=0",
                "/cgi-bin/mjpg/video.cgi?channel=1&subtype=1",
                "/cgi-bin/snapshot.cgi?channel=1",
            ],
            "snapshots": [
                "/cgi-bin/snapshot.cgi",
                "/cgi-bin/image.cgi",
            ],
            "auth_type": "digest",
            "default_creds": [("admin", "admin"), ("admin", "123456"), ("admin", "888888")]
        },
        "TP-Link": {
            "patterns": ["tp-link", "tplink", "nc", "tapocam"],
            "streams": [
                "/stream/get",
                "/video",
                "/live",
                "/mjpeg",
            ],
            "snapshots": [
                "/snapshot.jpg",
                "/image.jpg",
            ],
            "auth_type": "basic",
            "default_creds": [("admin", "admin"), ("admin", "1234")]
        },
        "Axis": {
            "patterns": ["axis", "m10", "m11", "p13", "q35"],
            "streams": [
                "/axis-cgi/mjpg/video.cgi",
                "/axis-cgi/mjpg/video.cgi?camera=1",
            ],
            "snapshots": [
                "/axis-cgi/jpg/image.cgi",
                "/axis-cgi/jpg/image.cgi?camera=1",
            ],
            "auth_type": "basic",
            "default_creds": [("root", "root"), ("root", "pass")]
        },
        "Foscam": {
            "patterns": ["foscam", "fi", "c1", "c2"],
            "streams": [
                "/videoMain",
                "/cgi-bin/CGIStream.cgi",
            ],
            "snapshots": [
                "/snapshot.jpg",
                "/cgi-bin/snapshot.cgi",
            ],
            "auth_type": "basic",
            "default_creds": [("admin", ""), ("admin", "admin")]
        },
        "Reolink": {
            "patterns": ["reolink", "rlc", "e1"],
            "streams": [
                "/bcs/channel0_main.bcs?channel=0&stream=0",
                "/bcs/channel1_sub.bcs?channel=1&stream=1",
            ],
            "snapshots": [
                "/bcs/channel0_main.bcs?channel=0&stream=0&snapshot=1",
            ],
            "auth_type": "basic",
            "default_creds": [("admin", ""), ("admin", "admin")]
        },
        "Annke": {
            "patterns": ["annke", "c800", "c500"],
            "streams": [
                "/cgi-bin/stream.cgi",
                "/video",
            ],
            "snapshots": [
                "/cgi-bin/snapshot.cgi",
            ],
            "auth_type": "basic",
            "default_creds": [("admin", "admin"), ("admin", "123456")]
        },
        "Vivotek": {
            "patterns": ["vivotek", "fd", "sd", "ib"],
            "streams": [
                "/cgi-bin/mjpg/video.cgi",
                "/video.mjpg",
            ],
            "snapshots": [
                "/cgi-bin/jpg/image.cgi",
            ],
            "auth_type": "digest",
            "default_creds": [("admin", "admin"), ("root", "root")]
        }
    }
    
    @classmethod
    def detect_brand(cls, html_content: str) -> str:
        """Detect camera brand from HTML content"""
        html_lower = html_content.lower()
        for brand, info in cls.BRANDS.items():
            for pattern in info["patterns"]:
                if pattern.lower() in html_lower:
                    return brand
        return "Generic"
    
    @classmethod
    def get_stream_urls(cls, brand: str, ip: str, with_auth: tuple = None) -> list:
        """Get stream URLs for detected brand"""
        urls = []
        brand_info = cls.BRANDS.get(brand, cls.BRANDS["Generic"] if "Generic" in cls.BRANDS else None)
        
        if not brand_info:
            brand_info = {"streams": ["/video", "/live", "/mjpeg", "/stream"]}
        
        for path in brand_info.get("streams", []):
            if with_auth and with_auth[0] and with_auth[1]:
                urls.append(f"http://{with_auth[0]}:{with_auth[1]}@{ip}{path}")
            urls.append(f"http://{ip}{path}")
        
        return urls


class AsyncFrameBuffer(QThread):
    """Asynchronous frame buffer for smooth video playback"""
    
    frame_ready = pyqtSignal(object)
    
    def __init__(self, stream_url: str, buffer_size: int = 2):
        super().__init__()
        self.stream_url = stream_url
        self.buffer_size = buffer_size
        self.running = True
        self.frame_queue = queue.Queue(maxsize=buffer_size)
        self.cap = None
        
    def run(self):
        """Background frame capture"""
        try:
            self.cap = cv2.VideoCapture(self.stream_url, cv2.CAP_FFMPEG)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            while self.running:
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        # Clear queue if full
                        if self.frame_queue.full():
                            try:
                                self.frame_queue.get_nowait()
                            except queue.Empty:
                                pass
                        self.frame_queue.put(frame)
                        self.frame_ready.emit(frame)
                else:
                    time.sleep(0.1)
        except Exception as e:
            print(f"Frame buffer error: {e}")
        finally:
            if self.cap:
                self.cap.release()
    
    def get_frame(self, timeout=0.033):
        """Get latest frame from buffer"""
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def stop(self):
        """Stop frame capture"""
        self.running = False
        if self.cap:
            self.cap.release()


class EnhancedHTTPCameraViewer(QMainWindow):
    """Enhanced HTTP camera viewer with professional features"""
    
    def __init__(self, device_ip: str):
        super().__init__()
        self.device_ip = device_ip
        self.stream_url = None
        self.buffer = None
        self.recording = False
        self.video_writer = None
        self.brand = "Generic"
        self.credentials = None
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        self.init_ui()
        self.start_connection()
    
    def init_ui(self):
        self.setWindowTitle(f"Enhanced CCTV Viewer - {self.device_ip}")
        self.setGeometry(100, 100, 1000, 750)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QLabel { color: #d4d4d4; }
            QPushButton { 
                background-color: #0e639c; 
                color: white; 
                border: none; 
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1177bb; }
            QPushButton:disabled { background-color: #3c3c3c; }
            QGroupBox { 
                border: 1px solid #3c3c3c; 
                border-radius: 5px; 
                margin-top: 10px;
                padding-top: 10px;
                color: #4ec9b0;
                font-weight: bold;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QLineEdit { 
                background-color: #2d2d30; 
                color: white; 
                border: 1px solid #3c3c3c;
                padding: 5px;
                border-radius: 3px;
            }
            QProgressBar {
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk { background-color: #4ec9b0; }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Video display area
        self.video_label = QLabel()
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setStyleSheet("background-color: #000000; border: 2px solid #4ec9b0; border-radius: 5px;")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.video_label)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("🔍 Initializing...")
        self.status_label.setStyleSheet("color: #e5c07b; padding: 5px;")
        status_layout.addWidget(self.status_label)
        
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setStyleSheet("color: #6a9955; padding: 5px;")
        status_layout.addWidget(self.fps_label)
        
        self.frame_label = QLabel("Frames: 0")
        self.frame_label.setStyleSheet("color: #6a9955; padding: 5px;")
        status_layout.addWidget(self.frame_label)
        
        main_layout.addLayout(status_layout)
        
        # Progress bar for connection
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Control panel
        control_group = QGroupBox("Controls")
        control_layout = QHBoxLayout(control_group)
        
        self.connect_btn = QPushButton("🔄 Reconnect")
        self.connect_btn.clicked.connect(self.reconnect)
        control_layout.addWidget(self.connect_btn)
        
        self.snapshot_btn = QPushButton("📸 Snapshot")
        self.snapshot_btn.clicked.connect(self.take_snapshot)
        control_layout.addWidget(self.snapshot_btn)
        
        self.record_btn = QPushButton("🎥 Record")
        self.record_btn.clicked.connect(self.toggle_recording)
        control_layout.addWidget(self.record_btn)
        
        self.browse_btn = QPushButton("🌐 Web Interface")
        self.browse_btn.clicked.connect(self.open_web)
        control_layout.addWidget(self.browse_btn)
        
        self.detect_btn = QPushButton("🔍 Auto-Detect")
        self.detect_btn.clicked.connect(self.auto_detect)
        control_layout.addWidget(self.detect_btn)
        
        control_layout.addStretch()
        main_layout.addWidget(control_group)
        
        # URL input
        url_group = QGroupBox("Manual Stream URL")
        url_layout = QHBoxLayout(url_group)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("http://ip:port/path or rtsp://ip:port/stream")
        url_layout.addWidget(self.url_input)
        
        self.apply_btn = QPushButton("Apply URL")
        self.apply_btn.clicked.connect(self.apply_url)
        url_layout.addWidget(self.apply_btn)
        
        main_layout.addWidget(url_group)
        
        # Debug panel (collapsible)
        self.debug_group = QGroupBox("Debug Console")
        self.debug_group.setCheckable(True)
        self.debug_group.setChecked(False)
        debug_layout = QVBoxLayout(self.debug_group)
        
        self.debug_text = QTextEdit()
        self.debug_text.setMaximumHeight(150)
        self.debug_text.setReadOnly(True)
        self.debug_text.setStyleSheet("background-color: #1e1e1e; font-family: monospace; font-size: 10px;")
        debug_layout.addWidget(self.debug_text)
        
        main_layout.addWidget(self.debug_group)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
    
    def debug(self, msg: str, level: str = "INFO"):
        """Add debug message with timestamp"""
        colors = {"INFO": "#6a9955", "WARN": "#e5c07b", "ERROR": "#f48771", "SUCCESS": "#4ec9b0"}
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted = f'<span style="color: {colors.get(level, "#d4d4d4")};">[{timestamp}] [{level}] {msg}</span>'
        self.debug_text.append(formatted)
        print(f"[{timestamp}] [{level}] {msg}")
        QApplication.processEvents()
    
    def start_connection(self):
        """Start connection process"""
        self.debug("Starting camera connection process...")
        self.auto_detect()
    
    def auto_detect(self):
        """Auto-detect camera brand and stream URL"""
        self.debug("Auto-detecting camera configuration...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        
        # Step 1: Detect brand from web interface
        self.progress_bar.setValue(20)
        brand = self.detect_brand()
        self.brand = brand
        self.debug(f"Detected brand: {brand}", "SUCCESS")
        
        # Step 2: Try default credentials
        self.progress_bar.setValue(30)
        creds = self.try_default_credentials()
        
        if creds:
            self.credentials = creds
            self.debug(f"Credentials found: {creds[0]}:{creds[1]}", "SUCCESS")
            self.status_label.setText(f"✅ Authenticated as {creds[0]}")
        else:
            self.debug("No default credentials worked", "WARN")
        
        # Step 3: Discover stream URL
        self.progress_bar.setValue(50)
        stream_url = self.discover_stream_url()
        
        if stream_url:
            self.stream_url = stream_url
            self.debug(f"Stream URL found: {stream_url}", "SUCCESS")
            self.progress_bar.setValue(80)
            self.start_stream()
        else:
            self.debug("No stream URL found automatically", "ERROR")
            self.status_label.setText("❌ Auto-detection failed - Enter URL manually")
            self.status_label.setStyleSheet("color: #f48771; padding: 5px;")
        
        self.progress_bar.setVisible(False)
    
    def detect_brand(self) -> str:
        """Detect camera brand from web interface"""
        try:
            url = f"http://{self.device_ip}"
            resp = requests.get(url, timeout=3, verify=False)
            if resp.status_code == 200:
                brand = CameraDatabase.detect_brand(resp.text)
                return brand
        except Exception as e:
            self.debug(f"Brand detection failed: {e}", "WARN")
        return "Generic"
    
    def try_default_credentials(self) -> tuple:
        """Try default credentials for detected brand"""
        brand_info = CameraDatabase.BRANDS.get(self.brand, {})
        default_creds = brand_info.get("default_creds", [("admin", "admin")])
        
        # Also try generic defaults
        generic_creds = [("admin", ""), ("admin", "admin"), ("admin", "123456"), ("root", "root")]
        all_creds = list(set(default_creds + generic_creds))
        
        for username, password in all_creds[:10]:  # Limit attempts
            self.debug(f"Testing credentials: {username}:{password}")
            try:
                url = f"http://{self.device_ip}"
                resp = requests.get(url, auth=(username, password), timeout=2, verify=False)
                if resp.status_code == 200 and len(resp.text) > 100:
                    # Check if login was successful (not redirected)
                    if "login" not in resp.text.lower() or "error" not in resp.text.lower():
                        return (username, password)
            except:
                pass
        return None
    
    def discover_stream_url(self) -> str:
        """Discover working stream URL"""
        self.debug("Searching for stream URL...")
        
        # Get brand-specific URLs
        urls_to_try = CameraDatabase.get_stream_urls(self.brand, self.device_ip, self.credentials)
        
        # Add generic URLs
        generic_paths = [
            "/video", "/live", "/mjpeg", "/stream", "/cgi-bin/mjpg/video.cgi",
            "/axis-cgi/mjpg/video.cgi", "/cgi-bin/video.cgi", "/videostream.cgi",
            "/cgi-bin/snapshot.cgi", "/snapshot.jpg", "/image.jpg",
        ]
        
        for path in generic_paths:
            if self.credentials:
                urls_to_try.append(f"http://{self.credentials[0]}:{self.credentials[1]}@{self.device_ip}{path}")
            urls_to_try.append(f"http://{self.device_ip}{path}")
        
        # Remove duplicates
        urls_to_try = list(OrderedDict.fromkeys(urls_to_try))
        
        # Test each URL with timeout
        for i, url in enumerate(urls_to_try[:30]):  # Limit to 30 attempts
            self.debug(f"Testing [{i+1}/{min(30, len(urls_to_try))}]: {url[:80]}...")
            
            try:
                # Quick test with OpenCV
                cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    cap.release()
                    if ret and frame is not None and frame.size > 1000:
                        self.debug(f"✓ Working stream found!", "SUCCESS")
                        return url
            except:
                pass
            
            # Update progress
            self.progress_bar.setValue(50 + int((i / 30) * 30))
        
        return None
    
    def start_stream(self):
        """Start asynchronous video stream"""
        if not self.stream_url:
            return
        
        self.debug(f"Starting stream: {self.stream_url}")
        
        # Start async frame buffer
        self.buffer = AsyncFrameBuffer(self.stream_url)
        self.buffer.frame_ready.connect(self.on_frame_received)
        self.buffer.start()
        
        self.status_label.setText(f"✅ Streaming from {self.device_ip} ({self.brand})")
        self.status_label.setStyleSheet("color: #4ec9b0; padding: 5px;")
        self.debug("Stream started successfully", "SUCCESS")
    
    def on_frame_received(self, frame):
        """Handle received frame"""
        self.frame_count += 1
        self.frame_label.setText(f"Frames: {self.frame_count}")
        
        # Calculate FPS
        now = time.time()
        if now - self.last_fps_time >= 1.0:
            self.fps = self.frame_count / (now - self.last_fps_time)
            self.fps_label.setText(f"FPS: {self.fps:.1f}")
            self.last_fps_time = now
            self.frame_count = 0
        
        # Resize frame if needed
        if frame.shape[1] > 800:
            scale = 800 / frame.shape[1]
            new_w = int(frame.shape[1] * scale)
            new_h = int(frame.shape[0] * scale)
            frame = cv2.resize(frame, (new_w, new_h))
        
        # Convert for Qt display
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        # Scale to fit label
        scaled = pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.video_label.setPixmap(scaled)
        
        # Record if enabled
        if self.recording and self.video_writer:
            self.video_writer.write(frame)
    
    def apply_url(self):
        """Apply manually entered URL"""
        manual_url = self.url_input.text().strip()
        if not manual_url:
            return
        
        if not manual_url.startswith(('http://', 'https://', 'rtsp://')):
            manual_url = f"http://{manual_url}"
        
        self.debug(f"Applying manual URL: {manual_url}")
        self.stream_url = manual_url
        
        if self.buffer:
            self.buffer.stop()
            self.buffer.wait()
        
        self.start_stream()
    
    def reconnect(self):
        """Reconnect to camera"""
        self.debug("Reconnecting...")
        if self.buffer:
            self.buffer.stop()
            self.buffer.wait()
        self.start_connection()
    
    def take_snapshot(self):
        """Save current frame as image"""
        if self.video_label.pixmap():
            filename = f"snapshot_{self.device_ip}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.video_label.pixmap().save(filename)
            self.status_bar.showMessage(f"📸 Snapshot saved: {filename}", 3000)
            self.debug(f"Snapshot saved: {filename}", "SUCCESS")
    
    def toggle_recording(self):
        """Toggle video recording"""
        if not self.recording:
            filename = f"recording_{self.device_ip}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(filename, fourcc, 15.0, (640, 480))
            self.recording = True
            self.record_btn.setText("⏹️ Stop Recording")
            self.record_btn.setStyleSheet("background-color: #d32f2f;")
            self.status_bar.showMessage(f"🎥 Recording to {filename}", 3000)
            self.debug(f"Started recording: {filename}", "SUCCESS")
        else:
            self.recording = False
            if self.video_writer:
                self.video_writer.release()
            self.record_btn.setText("🎥 Record")
            self.record_btn.setStyleSheet("")
            self.status_bar.showMessage("Recording stopped", 3000)
            self.debug("Recording stopped")
    
    def open_web(self):
        """Open camera web interface"""
        import webbrowser
        url = f"http://{self.device_ip}"
        webbrowser.open(url)
        self.debug(f"Opened web interface: {url}")
    
    def closeEvent(self, event):
        """Clean up on close"""
        self.debug("Shutting down...")
        if self.buffer:
            self.buffer.stop()
            self.buffer.wait()
        if self.recording and self.video_writer:
            self.video_writer.release()
        event.accept()


class CredentialTester(QDialog):
    """Dialog for testing credentials manually"""
    
    def __init__(self, ip: str, parent=None):
        super().__init__(parent)
        self.ip = ip
        self.result = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(f"Test Credentials - {self.ip}")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel(f"Testing camera: {self.ip}"))
        
        form = QFormLayout()
        self.username_input = QLineEdit("admin")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Username:", self.username_input)
        form.addRow("Password:", self.password_input)
        layout.addLayout(form)
        
        buttons = QHBoxLayout()
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self.test)
        buttons.addWidget(test_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        layout.addLayout(buttons)
        
        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)
    
    def test(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        try:
            url = f"http://{self.ip}"
            resp = requests.get(url, auth=(username, password), timeout=3, verify=False)
            if resp.status_code == 200:
                self.result_label.setText(f"✅ Success! Connected as {username}:{password}")
                self.result_label.setStyleSheet("color: #4ec9b0;")
                self.result = (username, password)
                QTimer.singleShot(1500, self.accept)
            else:
                self.result_label.setText(f"❌ Failed! Status code: {resp.status_code}")
                self.result_label.setStyleSheet("color: #f48771;")
        except Exception as e:
            self.result_label.setText(f"❌ Error: {e}")
            self.result_label.setStyleSheet("color: #f48771;")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Show splash screen
    splash = QSplashScreen()
    splash.setPixmap(QPixmap(400, 200))
    splash.show()
    splash.showMessage("CCTV Security Assessment Suite v3.0", Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)
    
    # Get camera IP
    ip, ok = QInputDialog.getText(None, "Camera Connection", 
                                   "Enter camera IP address:",
                                   text="192.168.1.1")
    
    splash.finish(None)
    
    if not ok or not ip:
        print("No IP entered")
        sys.exit(1)
    
    viewer = EnhancedHTTPCameraViewer(ip)
    viewer.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
