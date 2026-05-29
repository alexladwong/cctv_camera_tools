

# Install required packages
pip install requests ipaddress

# For RTSP testing (optional)
sudo apt install ffmpeg


# Scan a single IP
python3 cctv_assessment.py 192.168.1.100

# Scan entire subnet
python3 cctv_assessment.py 192.168.1.0/24

# Save to custom report file
python3 cctv_assessment.py 192.168.1.0/24 --output office_cctv_report.json

# Step 1: Map your CCTV network
python3 cctv_assessment.py 10.0.0.0/24 --output initial_map.json

# Step 2: Identify vulnerable devices
# Review the generated HTML report

# Step 3: Document findings for remediation
# Provide report to IT security team

# Step 4: (With permission) Test critical findings manually




# Install all required packages
pip install PyQt6 opencv-python numpy scapy requests

# For camera stream viewing
sudo apt install ffmpeg

# Run the application
python3 cctv_assessment_suite.py
