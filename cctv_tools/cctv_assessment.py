#!/usr/bin/env python3
"""
CCTV Security Assessment Framework - Professional Edition
For AUTHORIZED penetration testing only
Use only on systems you own or have written permission to test

Features:
  - Default credential testing
  - RTSP stream vulnerability assessment  
  - ONVIF protocol analysis
  - Firmware version detection
  - Open port scanning
  - Vulnerability enumeration
"""

import socket
import requests
import base64
import struct
import hashlib
import threading
import ipaddress
import urllib3
import json
import time
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass
class Vulnerability:
    name: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    description: str
    remediation: str
    cve_id: Optional[str] = None

@dataclass
class CCTVDevice:
    ip: str
    port: int
    model: str = "Unknown"
    firmware: str = "Unknown"
    vulnerabilities: List[Vulnerability] = None
    open_ports: List[int] = None
    
    def __post_init__(self):
        if self.vulnerabilities is None:
            self.vulnerabilities = []
        if self.open_ports is None:
            self.open_ports = []

class CCTVPenetrationTester:
    """Authorized CCTV Security Assessment Tool"""
    
    # Common CCTV default credentials (for testing only)
    DEFAULT_CREDENTIALS = [
        ("admin", ""),
        ("admin", "admin"),
        ("admin", "123456"),
        ("admin", "password"),
        ("admin", "12345"),
        ("root", "root"),
        ("root", ""),
        ("user", "user"),
        ("admin", "888888"),
        ("admin", "666666"),
        ("admin", "111111"),
        ("administrator", "password"),
        ("guest", "guest"),
        ("default", "default"),
        ("admin", "1234"),
        ("admin", "admin123"),
        ("Admin", "Admin"),
        ("supervisor", "supervisor"),
        ("service", "service"),
    ]
    
    # Common CCTV ports
    CCTV_PORTS = {
        80: "HTTP",
        443: "HTTPS",
        554: "RTSP",
        8000: "HTTP Alt",
        8080: "HTTP Proxy",
        8443: "HTTPS Alt",
        37777: "Dahua",
        37778: "Dahua HTTPS",
        34567: "Hikvision",
        34599: "Hikvision HTTPS",
        81: "Web Interface",
        82: "Web Interface",
        88: "Web Interface",
        7001: "Web Interface",
        7002: "Web Interface",
        8554: "RTSP Alt",
        1935: "RTMP",
        7070: "RTSP Alt",
        10554: "RTSP Alt",
        3000: "HTTP Alt",
        5000: "HTTP Alt",
        9091: "Web Interface",
        10080: "HTTP Alt",
        20000: "Web Interface",
    }
    
    # Known vulnerability patterns
    VULNERABILITY_PATTERNS = {
        "Hikvision": {
            "backdoor": "/System/configurationFile?auth=YWRtaW46MTEK",
            "info_leak": "/Security/users?auth=YWRtaW46MTEK",
        },
        "Dahua": {
            "auth_bypass": "/current_config/config",
        },
        "generic": {
            "cgi_leak": "/cgi-bin/status.cgi",
            "snapshot": "/snapshot.cgi",
        }
    }
    
    def __init__(self, target_network: str, output_file: str = "cctv_assessment_report.json"):
        """
        Initialize the CCTV assessment tool
        
        Args:
            target_network: IP or CIDR range (e.g., "192.168.1.0/24" or "192.168.1.100")
            output_file: Path to save assessment report
        """
        self.target_network = target_network
        self.output_file = output_file
        self.devices: List[CCTVDevice] = []
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'CCTV-Security-Scanner/1.0 (Security Assessment)'
        })
        
    def discover_devices(self) -> List[str]:
        """Discover CCTV devices on the network using multiple methods"""
        discovered = set()
        
        # Parse network range
        try:
            if '/' in self.target_network:
                network = ipaddress.ip_network(self.target_network, strict=False)
                ips = [str(ip) for ip in network.hosts()]
            else:
                ips = [self.target_network]
        except ValueError:
            print(f"[!] Invalid network format: {self.target_network}")
            return []
        
        print(f"[*] Scanning {len(ips)} IP addresses for CCTV devices...")
        
        # Multi-threaded scanning
        def scan_ip(ip):
            for port in [80, 443, 554, 8080, 37777, 34567]:
                if self.check_port(ip, port):
                    discovered.add(ip)
                    print(f"  [+] Found device: {ip}:{port}")
                    break
        
        threads = []
        for ip in ips[:254]:  # Limit to first 254 for speed
            t = threading.Thread(target=scan_ip, args=(ip,))
            t.start()
            threads.append(t)
            time.sleep(0.01)  # Rate limiting
        
        for t in threads:
            t.join(timeout=2)
        
        return list(discovered)
    
    def check_port(self, ip: str, port: int, timeout: float = 1.0) -> bool:
        """Check if a port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def scan_ports(self, ip: str) -> List[int]:
        """Scan common CCTV ports on a device"""
        open_ports = []
        print(f"  [*] Scanning ports for {ip}...")
        
        for port in self.CCTV_PORTS.keys():
            if self.check_port(ip, port, timeout=0.5):
                open_ports.append(port)
                print(f"    → Port {port} ({self.CCTV_PORTS.get(port, 'Unknown')}) open")
        
        return open_ports
    
    def test_rtsp_vulnerability(self, ip: str, port: int = 554) -> Dict:
        """Test RTSP stream vulnerabilities"""
        results = {"vulnerable": False, "streams": [], "anonymous": False}
        
        # Test anonymous RTSP access
        test_paths = [
            "/",
            "/live",
            "/stream",
            "/h264",
            "/h264ESVideoTrack",
            "/h264ESVideoTrack?tcp",
            "/live/ch0",
            "/live/0",
            "/streaming/channels/1",
            "/cam/realmonitor?channel=1&subtype=0",
            "/video",
            "/live?channel=1",
            "/axis-media/media.amp",
            "/mjpeg",
        ]
        
        for path in test_paths[:5]:  # Limit for speed
            try:
                url = f"rtsp://{ip}:{port}{path}"
                # This is a simplified test - real RTSP requires proper client
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((ip, port))
                
                # Send RTSP OPTIONS request
                request = f"OPTIONS {path} RTSP/1.0\r\nCSeq: 1\r\n\r\n"
                sock.send(request.encode())
                response = sock.recv(1024).decode()
                sock.close()
                
                if "200 OK" in response:
                    results["vulnerable"] = True
                    results["anonymous"] = True
                    results["streams"].append({"path": path, "type": "anonymous_access"})
                    print(f"    ⚠️  Anonymous RTSP access at {path}")
            except:
                pass
        
        return results
    
    def test_web_interface(self, ip: str, port: int) -> Dict:
        """Test web interface for vulnerabilities"""
        results = {"vulnerable_endpoints": [], "credentials_found": [], "info_leak": False}
        
        urls_to_test = [
            f"http://{ip}:{port}",
            f"https://{ip}:{port}",
            f"http://{ip}:{port}/login.cgi",
            f"http://{ip}:{port}/cgi-bin/login",
            f"http://{ip}:{port}/web/login.html",
        ]
        
        # Test default credentials
        for username, password in self.DEFAULT_CREDENTIALS:
            try:
                # Try form-based login
                login_data = {
                    "username": username,
                    "password": password,
                    "user": username,
                    "pass": password,
                    "login": "Login"
                }
                
                for url in urls_to_test[:2]:
                    try:
                        resp = self.session.post(url, data=login_data, timeout=3)
                        # Check for successful login indicators
                        if resp.status_code == 200 and any(indicator in resp.text.lower() 
                           for indicator in ["dashboard", "status", "live", "camera", "stream"]):
                            results["credentials_found"].append({
                                "url": url,
                                "username": username,
                                "password": password
                            })
                            print(f"    ✅ DEFAULT CREDENTIALS: {username}:{password}")
                    except:
                        pass
            except:
                pass
        
        # Test for information disclosure
        leak_paths = [
            "/config/get_conf",
            "/config/configuration",
            "/cgi-bin/config.cgi",
            "/System/configurationFile",
            "/etc/passwd",
            "/proc/self/environ",
        ]
        
        for path in leak_paths:
            try:
                url = f"http://{ip}:{port}{path}"
                resp = self.session.get(url, timeout=2)
                if resp.status_code == 200 and len(resp.text) > 100:
                    results["info_leak"] = True
                    results["vulnerable_endpoints"].append({
                        "path": path,
                        "type": "information_disclosure"
                    })
                    print(f"    ⚠️  Potential info leak at {path}")
            except:
                pass
        
        return results
    
    def onvif_discovery(self, ip: str) -> Dict:
        """Test ONVIF protocol compliance and vulnerabilities"""
        results = {"onvif_supported": False, "services": [], "vulnerable": False}
        
        try:
            # ONVIF discovery probe
            probe = """<?xml version="1.0" encoding="UTF-8"?>
            <Envelope xmlns="http://www.w3.org/2003/05/soap-envelope">
              <Header>
                <wsa:MessageID xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">urn:uuid:test</wsa:MessageID>
                <wsa:To xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
                <wsa:Action xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
              </Header>
              <Body>
                <Probe xmlns="http://schemas.xmlsoap.org/ws/2005/04/discovery">
                  <Types>dn:NetworkVideoTransmitter</Types>
                </Probe>
              </Body>
            </Envelope>"""
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            sock.sendto(probe.encode(), (ip, 3702))
            
            try:
                data, addr = sock.recvfrom(4096)
                if data:
                    results["onvif_supported"] = True
                    print(f"    ✓ ONVIF device detected")
            except socket.timeout:
                pass
            sock.close()
        except:
            pass
        
        return results
    
    def identify_device_model(self, ip: str, open_ports: List[int]) -> Tuple[str, str]:
        """Attempt to identify device model and firmware version"""
        model = "Unknown"
        firmware = "Unknown"
        
        # Try to identify by HTTP headers
        for port in [80, 443, 8080, 8443]:
            if port in open_ports:
                try:
                    scheme = "https" if port in [443, 8443, 34599, 37778] else "http"
                    url = f"{scheme}://{ip}:{port}"
                    resp = self.session.get(url, timeout=3)
                    
                    # Check for model indicators in headers
                    headers = resp.headers
                    server = headers.get('Server', '')
                    
                    if 'hikvision' in server.lower():
                        model = "Hikvision"
                        firmware = server
                    elif 'dahua' in server.lower():
                        model = "Dahua"
                        firmware = server
                    elif 'axis' in server.lower():
                        model = "Axis"
                        firmware = server
                    
                    # Check in page content
                    if 'hikvision' in resp.text.lower():
                        model = "Hikvision"
                    elif 'dahua' in resp.text.lower():
                        model = "Dahua"
                    
                except:
                    pass
        
        return model, firmware
    
    def generate_vulnerabilities(self, device: CCTVDevice) -> List[Vulnerability]:
        """Generate vulnerability list based on findings"""
        vulnerabilities = []
        
        # Check for default credentials
        # (This is simplified - in practice you'd check actual found creds)
        
        # Check for outdated/known vulnerable models
        if device.model == "Hikvision" and device.firmware:
            vulnerabilities.append(Vulnerability(
                name="Hikvision Backdoor Vulnerability (2017)",
                severity="CRITICAL",
                description="Some Hikvision firmware versions have a backdoor allowing unauthorized access",
                remediation="Update firmware to latest version or apply security patches",
                cve_id="CVE-2017-7921"
            ))
        
        if device.model == "Dahua":
            vulnerabilities.append(Vulnerability(
                name="Dahua Authentication Bypass",
                severity="HIGH",
                description="Older Dahua firmware allows authentication bypass via crafted requests",
                remediation="Update firmware to version after 2020",
                cve_id="CVE-2019-3929"
            ))
        
        # Check open sensitive ports
        if 554 in device.open_ports:
            vulnerabilities.append(Vulnerability(
                name="Unsecured RTSP Stream",
                severity="MEDIUM",
                description="RTSP port open - may allow unauthorized video streaming if no authentication",
                remediation="Implement RTSP authentication or restrict access by IP",
                cve_id=None
            ))
        
        if 37777 in device.open_ports:
            vulnerabilities.append(Vulnerability(
                name="Dahua Default Port Exposure",
                severity="MEDIUM",
                description="Dahua private protocol port exposed",
                remediation="Change default port or restrict access",
                cve_id=None
            ))
        
        return vulnerabilities
    
    def assess_device(self, ip: str) -> CCTVDevice:
        """Complete security assessment of a single CCTV device"""
        print(f"\n[+] Assessing: {ip}")
        
        # Port scanning
        open_ports = self.scan_ports(ip)
        
        if not open_ports:
            print(f"  [!] No CCTV-related ports open")
            return None
        
        # Identify device
        model, firmware = self.identify_device_model(ip, open_ports)
        
        device = CCTVDevice(
            ip=ip,
            port=open_ports[0] if open_ports else 0,
            model=model,
            firmware=firmware,
            open_ports=open_ports
        )
        
        # Test RTSP
        if 554 in open_ports:
            rtsp_results = self.test_rtsp_vulnerability(ip)
            if rtsp_results.get("vulnerable"):
                device.vulnerabilities.append(Vulnerability(
                    name="Anonymous RTSP Access",
                    severity="HIGH",
                    description=f"RTSP stream accessible without authentication at {ip}:554",
                    remediation="Enable authentication for RTSP streams",
                    cve_id=None
                ))
        
        # Test web interface
        for port in [80, 443, 8080, 8443]:
            if port in open_ports:
                web_results = self.test_web_interface(ip, port)
                if web_results.get("credentials_found"):
                    device.vulnerabilities.append(Vulnerability(
                        name="Default Credentials",
                        severity="CRITICAL",
                        description=f"Default credentials found: {web_results['credentials_found']}",
                        remediation="Change all default passwords immediately",
                        cve_id=None
                    ))
        
        # ONVIF testing
        onvif_results = self.onvif_discovery(ip)
        if onvif_results.get("onvif_supported"):
            device.vulnerabilities.append(Vulnerability(
                name="ONVIF Service Exposed",
                severity="INFO",
                description="Device supports ONVIF protocol - check if authentication is required",
                remediation="Ensure ONVIF authentication is enabled",
                cve_id=None
            ))
        
        # Generate additional vulnerabilities based on model
        device.vulnerabilities.extend(self.generate_vulnerabilities(device))
        
        return device
    
    def run_assessment(self) -> Dict:
        """Run complete security assessment"""
        print("\n" + "=" * 70)
        print("CCTV SECURITY ASSESSMENT FRAMEWORK")
        print("=" * 70)
        print(f"Target: {self.target_network}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Discover devices
        discovered_ips = self.discover_devices()
        
        if not discovered_ips:
            print("\n[!] No CCTV devices discovered. Check network range and connectivity.")
            return {"error": "No devices found"}
        
        print(f"\n[*] Discovered {len(discovered_ips)} potential CCTV devices")
        
        # Assess each device
        for ip in discovered_ips:
            device = self.assess_device(ip)
            if device:
                self.devices.append(device)
        
        # Generate report
        report = self.generate_report()
        
        # Print summary
        self.print_summary(report)
        
        # Save report
        self.save_report(report)
        
        return report
    
    def generate_report(self) -> Dict:
        """Generate comprehensive assessment report"""
        report = {
            "title": "CCTV Security Assessment Report",
            "target_network": self.target_network,
            "scan_timestamp": datetime.now().isoformat(),
            "devices_found": len(self.devices),
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 0,
            "medium_vulnerabilities": 0,
            "low_vulnerabilities": 0,
            "devices": [],
            "recommendations": []
        }
        
        for device in self.devices:
            device_data = {
                "ip": device.ip,
                "model": device.model,
                "firmware": device.firmware,
                "open_ports": device.open_ports,
                "vulnerabilities": []
            }
            
            for vuln in device.vulnerabilities:
                vuln_data = asdict(vuln)
                device_data["vulnerabilities"].append(vuln_data)
                
                if vuln.severity == "CRITICAL":
                    report["critical_vulnerabilities"] += 1
                elif vuln.severity == "HIGH":
                    report["high_vulnerabilities"] += 1
                elif vuln.severity == "MEDIUM":
                    report["medium_vulnerabilities"] += 1
                else:
                    report["low_vulnerabilities"] += 1
            
            report["devices"].append(device_data)
        
        # Generate recommendations
        if report["critical_vulnerabilities"] > 0:
            report["recommendations"].append("🔴 IMMEDIATE ACTION: Change all default credentials on critical devices")
        if report["high_vulnerabilities"] > 0:
            report["recommendations"].append("🟠 Update firmware on all devices to latest versions")
        if any("RTSP" in str(d) for d in report["devices"]):
            report["recommendations"].append("🔵 Implement network segmentation for CCTV network")
        report["recommendations"].append("📋 Review access logs for unauthorized access attempts")
        report["recommendations"].append("🔒 Enable HTTPS and disable HTTP if possible")
        
        return report
    
    def print_summary(self, report: Dict):
        """Print assessment summary to console"""
        print("\n" + "=" * 70)
        print("ASSESSMENT SUMMARY")
        print("=" * 70)
        print(f"Devices Found: {report['devices_found']}")
        print(f"\nVulnerability Counts:")
        print(f"  🔴 CRITICAL: {report['critical_vulnerabilities']}")
        print(f"  🟠 HIGH: {report['high_vulnerabilities']}")
        print(f"  🟡 MEDIUM: {report['medium_vulnerabilities']}")
        print(f"  🔵 LOW: {report['low_vulnerabilities']}")
        
        print(f"\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
        
        print(f"\nDetailed report saved to: {self.output_file}")
        print("=" * 70)
    
    def save_report(self, report: Dict):
        """Save assessment report to JSON file"""
        with open(self.output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Also generate human-readable HTML report
        html_report = self.generate_html_report(report)
        html_file = self.output_file.replace('.json', '.html')
        with open(html_file, 'w') as f:
            f.write(html_report)
        print(f"HTML report saved to: {html_file}")
    
    def generate_html_report(self, report: Dict) -> str:
        """Generate HTML formatted report"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>CCTV Security Assessment Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #1e1e1e; color: #d4d4d4; }}
        .container {{ max-width: 1200px; margin: auto; background: #252526; padding: 20px; border-radius: 10px; }}
        h1, h2 {{ color: #4ec9b0; }}
        .critical {{ color: #f48771; font-weight: bold; }}
        .high {{ color: #e5c07b; }}
        .medium {{ color: #dcdcaa; }}
        .low {{ color: #6a9955; }}
        .device {{ background: #2d2d30; margin: 15px 0; padding: 15px; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #3c3c3c; padding: 8px; text-align: left; }}
        th {{ background: #0e639c; }}
        .timestamp {{ color: #6a9955; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📹 CCTV Security Assessment Report</h1>
        <p><strong>Target Network:</strong> {report['target_network']}</p>
        <p><strong>Scan Timestamp:</strong> {report['scan_timestamp']}</p>
        <p><strong>Devices Found:</strong> {report['devices_found']}</p>
        
        <h2>📊 Vulnerability Summary</h2>
        <p><span class="critical">🔴 CRITICAL: {report['critical_vulnerabilities']}</span></p>
        <p><span class="high">🟠 HIGH: {report['high_vulnerabilities']}</span></p>
        <p><span class="medium">🟡 MEDIUM: {report['medium_vulnerabilities']}</span></p>
        <p><span class="low">🔵 LOW: {report['low_vulnerabilities']}</span></p>
        
        <h2>🛡️ Recommendations</h2>
        <ul>
"""
        for rec in report['recommendations']:
            html += f"            <li>{rec}</li>\n"
        
        html += """        </ul>
        
        <h2>📡 Device Details</h2>
"""
        for device in report['devices']:
            html += f"""
        <div class="device">
            <h3>Device: {device['ip']}</h3>
            <p><strong>Model:</strong> {device['model']}</p>
            <p><strong>Firmware:</strong> {device['firmware']}</p>
            <p><strong>Open Ports:</strong> {', '.join(map(str, device['open_ports']))}</p>
"""
            if device['vulnerabilities']:
                html += """            <p><strong>Vulnerabilities Found:</strong></p>
            <table>
                <tr><th>Vulnerability</th><th>Severity</th><th>Description</th><th>Remediation</th></tr>
"""
                for vuln in device['vulnerabilities']:
                    severity_class = vuln['severity'].lower()
                    html += f"""                <tr>
                    <td>{vuln['name']}</td>
                    <td class="{severity_class}">{vuln['severity']}</td>
                    <td>{vuln['description']}</td>
                    <td>{vuln['remediation']}</td>
                </tr>
"""
                html += "            </table>\n"
            else:
                html += "            <p>✓ No significant vulnerabilities found</p>\n"
            html += "        </div>\n"
        
        html += f"""
        <hr>
        <p class="timestamp">Report generated by CCTV Security Assessment Framework</p>
        <p><em>This assessment was performed on {report['target_network']} for authorized security testing purposes.</em></p>
    </div>
</body>
</html>
"""
        return html
    
    def attack_stream_capture(self, ip: str, output_file: str = "capture.mp4"):
        """
        DEMONSTRATION ONLY: Show how streams could be captured
        This is for understanding attack vectors, not actual exploitation
        """
        print(f"\n[*] DEMONSTRATION: Potential RTSP stream capture from {ip}")
        print(f"    Command would be: ffmpeg -i rtsp://{ip}:554/stream -c copy {output_file}")
        print("    This is only possible if device has no authentication or default creds")
        return {
            "vulnerable": True,
            "potential_attack": "RTSP stream capture",
            "mitigation": "Enable RTSP authentication and use strong passwords"
        }

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='CCTV Security Assessment Framework - Authorized Testing Only',
        epilog="""
Examples:
  python cctv_assessment.py 192.168.1.0/24
  python cctv_assessment.py 192.168.1.100 --output report.json
        """
    )
    
    parser.add_argument('target', help='Target IP or CIDR network (e.g., 192.168.1.0/24)')
    parser.add_argument('--output', '-o', default='cctv_assessment_report.json', 
                       help='Output report file')
    parser.add_argument('--quick', '-q', action='store_true', 
                       help='Quick scan (reduced timeout)')
    
    args = parser.parse_args()
    
    # Confirmation for ethical use
    print("\n" + "=" * 70)
    print("⚠️  AUTHORIZATION REQUIRED")
    print("=" * 70)
    print("This tool is for AUTHORIZED penetration testing only.")
    print("You must have written permission to test the target network.")
    print("=" * 70)
    
    response = input("\nDo you have written authorization? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("\n[!] Authorization required. Exiting.")
        print("    For authorized testing, obtain written permission first.")
        sys.exit(1)
    
    # Run assessment
    tester = CCTVPenetrationTester(args.target, args.output)
    
    try:
        report = tester.run_assessment()
    except KeyboardInterrupt:
        print("\n\n[!] Assessment interrupted by user")
        tester.save_report({"error": "Interrupted", "partial": True})
    except Exception as e:
        print(f"\n[!] Error during assessment: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    main()
