#!/usr/bin/env python3
"""
Quick Camera Diagnostic Tool
Usage: python3 diagnose_camera.py <camera_ip>
"""

import sys
import socket
import subprocess
import cv2
import requests
import urllib3
urllib3.disable_warnings()

def diagnose_camera(ip):
    print(f"\n🔍 DIAGNOSING CAMERA: {ip}")
    print("=" * 50)
    
    # 1. Network connectivity
    print("\n📡 1. NETWORK CONNECTIVITY")
    result = subprocess.run(['ping', '-c', '2', '-W', '1', ip], capture_output=True)
    if result.returncode == 0:
        print("   ✅ Camera is reachable")
    else:
        print("   ❌ Camera is NOT reachable")
        return
    
    # 2. Port scanning
    print("\n🔌 2. OPEN PORTS")
    common_ports = [80, 443, 554, 8080, 8000, 37777, 34567, 8554, 1935]
    open_ports = []
    
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            if sock.connect_ex((ip, port)) == 0:
                open_ports.append(port)
                print(f"   ✅ Port {port} OPEN")
            sock.close()
        except:
            pass
    
    if not open_ports:
        print("   ❌ No common CCTV ports open")
    
    # 3. Try RTSP connection
    print("\n📹 3. RTSP STREAM TEST")
    rtsp_urls = [
        f"rtsp://{ip}:554",
        f"rtsp://{ip}:554/streaming/channels/1",
        f"rtsp://{ip}:554/live",
        f"rtsp://{ip}:554/h264",
        f"rtsp://{ip}:554/cam/realmonitor?channel=1&subtype=0",
    ]
    
    for url in rtsp_urls:
        try:
            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"   ✅ WORKING: {url}")
                    cap.release()
                    break
                else:
                    print(f"   ⚠️  Connected but no frame: {url[:60]}")
            cap.release()
        except Exception as e:
            print(f"   ❌ Failed: {url[:60]} - {str(e)[:30]}")
    
    # 4. Web interface check
    print("\n🌐 4. WEB INTERFACE")
    for port in [80, 8080, 8000]:
        try:
            url = f"http://{ip}:{port}"
            resp = requests.get(url, timeout=2, verify=False)
            if resp.status_code < 500:
                print(f"   ✅ Web interface on port {port}")
                # Detect brand
                text = resp.text.lower()
                if "hikvision" in text:
                    print(f"   ℹ️  Brand: Hikvision detected")
                elif "dahua" in text:
                    print(f"   ℹ️  Brand: Dahua detected")
                break
        except:
            pass
    
    print("\n" + "=" * 50)
    
    if open_ports:
        print("\n💡 SUGGESTED COMMANDS:")
        for port in open_ports:
            if port == 554:
                print(f"   ffplay rtsp://{ip}:554/streaming/channels/1")
            elif port in [80, 8080]:
                print(f"   firefox http://{ip}:{port}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        diagnose_camera(sys.argv[1])
    else:
        print("Usage: python3 diagnose_camera.py <camera_ip>")
        print("Example: python3 diagnose_camera.py 192.168.1.100")
