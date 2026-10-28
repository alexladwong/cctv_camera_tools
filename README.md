📹 CCTV Security Assessment Suite

CCTV Network Discovery, Security Auditing & Assessment Toolkit

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Interface-CLI%20%7C%20PyQt6-41B883" alt="CLI and PyQt6">
  <img src="https://img.shields.io/badge/Focus-CCTV%20%26%20Network%20Security-0A7D91" alt="CCTV and Network Security">
  <img src="https://img.shields.io/badge/Platform-Kali%20Linux-557C94" alt="Kali Linux">
  <img src="https://img.shields.io/badge/License-Verify%20Repository%20License-lightgrey" alt="License">
</p>---

📌 Overview

CCTV Security Assessment Suite is a Python-based toolkit for authorized CCTV network discovery, security assessment, camera diagnostics, and security report generation.

The project combines command-line assessment capabilities with a PyQt6 graphical application and supporting camera utilities.

It is intended for security professionals, network administrators, cybersecurity students, and authorized penetration testers who need to investigate CCTV deployments, document potential weaknesses, and support remediation.

Project objectives

- Discover and assess authorized CCTV network targets.
- Organize device information and security findings.
- Support camera-related diagnostics and stream viewing.
- Generate and review assessment reports.
- Provide both command-line and graphical workflows.
- Support repeatable security assessments in controlled environments.

«Authorization required: Only assess CCTV devices and networks that you own or have explicit permission to test. Network scanning, traffic interception, and camera stream access may affect device availability or expose sensitive information.»

---

✨ Features

1. Command-Line Assessment

The CLI assessment engine accepts individual IP addresses and CIDR network ranges.

Confirmed command-line options include:

Option| Description
"target"| Target IP address or CIDR network
"-h", "--help"| Display command-line help
"-o", "--output OUTPUT"| Specify the output report file
"-q", "--quick"| Use reduced timeouts

Example:

python cctv_assessment.py --help

2. Graphical Assessment Suite

The desktop application uses PyQt6 and contains components for:

- CCTV device representation.
- Security finding representation.
- Background assessment tasks.
- Firmware-related analysis.
- Traffic-related functionality.
- Live stream viewing.
- Graphical assessment workflows.

The actual availability of individual operations depends on their implementation, device compatibility, and the runtime environment.

3. Camera Diagnostics and Viewing

Supporting scripts provide a foundation for camera-related diagnostics and viewing workflows.

These utilities should be tested against authorized devices before being relied upon in production.

4. Assessment Reports

The project includes JSON and HTML report files.

These formats support structured data review and human-readable reporting. Report fields and assessment coverage should be verified against the current implementation.

---

🧰 Project Structure

The following files have been identified in the project directory.

cctv_tools/
├── README.md
├── README.txt
│
├── cctv_assessment.py
├── cctv_assessment_suite.py
│
├── diagnose_camera.py
├── enhanced_cctv_viewer.py
│
├── test_camera_http.py
├── test_camera_htt.py
│
├── cctv_assessment_report.html
├── cctv_assessment_report.json
├── cctv_report_20260528_094625.json
│
├── office_cctv_report.html
├── office_cctv_report.json
│
└── .venv/

The ".venv/" directory is created during local installation and should generally be excluded from version control.

Main components

File| Purpose
"cctv_assessment.py"| Command-line assessment framework
"cctv_assessment_suite.py"| PyQt6 graphical assessment application
"diagnose_camera.py"| Camera diagnostic utility
"enhanced_cctv_viewer.py"| Enhanced camera viewing utility
"test_camera_http.py"| HTTP-related camera testing utility
"test_camera_htt.py"| Additional HTTP-related utility; verify its intended purpose

The repository also contains sample or previously generated HTML and JSON reports.

---

💻 Requirements

Recommended environment

- Python 3.10 or later, subject to compatibility testing.
- pip.
- A supported Linux environment for network assessment.
- PyQt6 for the desktop application.
- OpenCV for image and video operations.
- NumPy for numerical and image-processing operations.
- Requests for HTTP operations.
- Scapy for packet and network operations.
- A graphical desktop environment for visible PyQt6 windows.

Kali Linux is a convenient environment for authorized cybersecurity testing.

Other operating systems may work, but platform-specific dependencies and network permissions should be verified.

Important Android and Kali note

Running Kali Linux inside Termux or a proot environment does not automatically provide a graphical desktop.

The command-line assessment may run without a GUI, while the desktop application requires a compatible graphical display.

A VNC desktop or another supported display environment may be necessary when running the GUI on Android.

---

🚀 Installation

Step 1: Navigate to the project

cd ~/CyberLab/Tools/cctv_camera_tools/cctv_tools

Step 2: Create a virtual environment

python3 -m venv .venv
source .venv/bin/activate

If virtual environment creation fails because the required Python components are missing, install the appropriate packages for your Linux distribution.

On Kali Linux:

apt update
apt install -y python3-venv python3-full

Then create and activate the environment again.

Step 3: Upgrade pip

python -m pip install --upgrade pip

Step 4: Install dependencies

Install the dependencies used by the current project:

python -m pip install requests ipaddress
python -m pip install PyQt6 opencv-python numpy scapy

Note: "ipaddress" is part of the Python standard library in supported Python versions, so a separate installation is normally unnecessary.

For video-related utilities, FFmpeg may also be useful.

On Kali Linux:

apt install -y ffmpeg

Step 5: Verify the installation

Check OpenCV:

python -c "import cv2; print('OpenCV:', cv2.__version__)"

Check the other principal dependencies:

python -c "import PyQt6, numpy, requests, scapy; print('Dependencies OK')"

Check the CLI:

python cctv_assessment.py --help

If these checks pass, the corresponding imports and CLI argument parser are available.

This does not, by itself, establish that every assessment feature works correctly.

---

🖥️ Command-Line Usage

Activate the virtual environment before running the application:

cd ~/CyberLab/Tools/cctv_camera_tools/cctv_tools
source .venv/bin/activate

Display help

python cctv_assessment.py --help

Assess an individual IP address

Only use a device you own or are authorized to assess.

python cctv_assessment.py 192.168.1.100

Use quick mode

python cctv_assessment.py --quick 192.168.1.100

Quick mode uses reduced timeouts. The precise checks performed and the effect on coverage depend on the implementation.

Specify an output report

python cctv_assessment.py \
  192.168.1.100 \
  --output camera_report.json

Assess an authorized subnet

python cctv_assessment.py \
  192.168.1.0/24 \
  --output office_cctv_report.json

A subnet assessment can contact multiple devices. Confirm the authorized scope and account for network load before running it.

Use quick mode with a subnet

python cctv_assessment.py \
  --quick \
  192.168.1.0/24 \
  --output quick_assessment.json

Use the short options

The supported short options are "-o" and "-q".

python cctv_assessment.py \
  -q \
  192.168.1.100 \
  -o camera_report.json

Verify the generated report

After an assessment, check whether the expected file exists:

ls -lh camera_report.json

If the output is JSON, validate its syntax:

python -m json.tool camera_report.json

A successful JSON parse confirms that the file is syntactically valid JSON. It does not establish the accuracy or completeness of its findings.

---

🖱️ Launching the Graphical Application

The main graphical application is:

cctv_assessment_suite.py

Launch it from the project directory:

cd ~/CyberLab/Tools/cctv_camera_tools/cctv_tools
source .venv/bin/activate

python cctv_assessment_suite.py

Graphical environment requirements

A PyQt6 application needs an appropriate Qt platform plugin and, for a visible desktop window, access to a graphical display.

Check the current environment:

echo "DISPLAY=${DISPLAY:-not set}"
echo "WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-not set}"
echo "QT_QPA_PLATFORM=${QT_QPA_PLATFORM:-not set}"

Check whether Qt can initialize:

python -c "from PyQt6.QtWidgets import QApplication; import sys; app = QApplication(sys.argv); print('Qt platform:', app.platformName())"

If the platform is reported as "offscreen", Qt is running without a normal visible window.

The offscreen platform can be useful for automated tests, but it is not a substitute for a desktop display.

If the GUI does not appear, verify the graphical environment before reinstalling Python dependencies.

---

📷 Camera Diagnostics and Viewing

The project contains two camera-related utilities:

diagnose_camera.py
enhanced_cctv_viewer.py

Inspect their available arguments before running them:

python diagnose_camera.py --help
python enhanced_cctv_viewer.py --help

These scripts may not implement "--help". If either command starts an application or reports an argument error, inspect the script's entry point and documentation instead.

For a source-level overview:

grep -nE 'ArgumentParser|add_argument|def main|if __name__' \
  diagnose_camera.py enhanced_cctv_viewer.py

Camera access considerations

- Use authorized camera addresses and credentials.
- Do not publish credentials, private stream URLs, or authentication tokens.
- Avoid testing camera endpoints outside your authorized scope.
- Consider the privacy implications of storing or displaying video.
- Verify that diagnostic requests do not interrupt normal camera operation.

Stream viewing depends on the protocols, codecs, authentication methods, and runtime capabilities implemented by the application.

---

📊 Reports and Results

The project directory contains these report files:

cctv_assessment_report.html
cctv_assessment_report.json
cctv_report_20260528_094625.json
office_cctv_report.html
office_cctv_report.json

These are existing project files. Their presence does not necessarily mean that a particular assessment completed successfully.

JSON reports

JSON is suitable for structured assessment results and subsequent processing.

Inspect the top-level fields:

python - <<'PY'
import json
from pathlib import Path

for path in sorted(Path(".").glob("*.json")):
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)

        print(f"\n{path}")

        if isinstance(data, dict):
            print("Keys:", ", ".join(data.keys()))
        elif isinstance(data, list):
            print("Entries:", len(data))
        else:
            print("Data type:", type(data).__name__)

    except (OSError, json.JSONDecodeError) as exc:
        print(f"{path}: {exc}")
PY

HTML reports

HTML reports are suitable for human-readable assessment summaries.

On a desktop environment, open a report in your preferred browser.

For example:

xdg-open cctv_assessment_report.html

This requires a compatible graphical desktop and an available browser.

Reporting best practices

A useful security assessment report should distinguish:

- Observed facts.
- Potential vulnerabilities.
- Confirmed vulnerabilities.
- Evidence and limitations.
- Severity and potential impact.
- Recommended remediation.
- Verification status.

Do not treat a detected open port, an HTTP response, or a camera banner as proof that a device is vulnerable.

---

🔍 Assessment Workflow

A responsible CCTV security assessment can follow these stages.

Stage 1: Define the scope

Document the authorized network ranges, device owners, testing window, and any prohibited actions.

Stage 2: Inventory devices

Use the assessment CLI to investigate the approved targets.

Record relevant device identifiers and observed services where supported by the implementation.

Stage 3: Review findings

Inspect the generated reports and validate significant findings.

Separate verified issues from indicators that require further investigation.

Stage 4: Validate critical findings

Perform additional manual verification only when authorized.

Prefer non-disruptive checks and avoid unnecessary access to live video or sensitive information.

Stage 5: Remediate

Depending on the verified issue, appropriate actions may include:

- Updating camera firmware.
- Changing default or weak credentials.
- Restricting administrative interfaces.
- Segmenting CCTV devices from user networks.
- Limiting access to camera management services.
- Disabling unnecessary services.
- Restricting camera streams to authorized clients.
- Reviewing logging and access controls.

Stage 6: Retest

Repeat the relevant checks after remediation and document whether the issue has been resolved.

---

🛠️ Troubleshooting

"ModuleNotFoundError: No module named 'cv2'"

Activate the project's virtual environment:

source .venv/bin/activate

Install OpenCV inside that environment:

python -m pip install opencv-python

Verify:

python -c "import cv2; print(cv2.__version__)"

"ModuleNotFoundError: No module named 'PyQt6'"

source .venv/bin/activate
python -m pip install PyQt6

Qt reports "propagateSizeHints()"

A message such as:

This plugin does not support propagateSizeHints()

can be a platform-plugin warning rather than a fatal exception.

Check whether the application remains responsive and whether a window is visible. Investigate the display configuration if it does not appear.

Qt reports "offscreen"

Check:

echo "$QT_QPA_PLATFORM"
echo "$DISPLAY"
echo "$WAYLAND_DISPLAY"

If "QT_QPA_PLATFORM" is explicitly set to "offscreen", and you have a functioning graphical desktop, try:

unset QT_QPA_PLATFORM
python cctv_assessment_suite.py

Only do this when a compatible display is available. Unsetting the variable cannot create a graphical desktop that does not exist.

The GUI is unavailable on Android

A Linux terminal alone does not guarantee graphical application support.

Configure a compatible desktop environment, such as a VNC desktop, before attempting to run the PyQt6 interface.

The CLI can be used independently where its networking and Python requirements are satisfied.

Report output is missing

Check the command's exit status and output:

echo $?

Then verify the specified path:

ls -lh camera_report.json

Use the actual filename supplied to "--output".

Python package installation fails

Ensure the virtual environment is active:

source .venv/bin/activate
python -m pip --version

Avoid forcing package installations into Kali's system-managed Python environment.

---

🔐 Security and Responsible Use

This toolkit is intended for legitimate security assessment, defensive research, and authorized testing.

Users are responsible for complying with applicable laws, organizational policies, privacy requirements, and contractual restrictions.

Do not use the toolkit to:

- Access cameras without authorization.
- Obtain or expose private video feeds.
- Capture credentials or sensitive traffic belonging to others.
- Disrupt CCTV operations or interfere with safety systems.
- Evade access controls or conceal unauthorized activity.
- Scan networks outside the approved scope.

Traffic-related functionality should only be used in an explicitly authorized environment with appropriate safeguards.

Protect assessment reports because they may contain sensitive device information, network addresses, and security weaknesses.

---

🧪 Development and Verification

Before releasing changes, verify the environment and available commands.

Check the CLI

python cctv_assessment.py --help

Check imports

python -c "import cv2, numpy, requests, scapy; print('Core dependencies OK')"

python -c "import PyQt6; print('PyQt6 OK')"

Check report syntax

python -m json.tool cctv_assessment_report.json > /dev/null

Repeat this check using the actual report generated during testing.

Check the Git working tree

git status --short

Keep generated reports, credentials, local configuration, and virtual environments out of version control when they contain sensitive information or unnecessary local artifacts.

A ".gitignore" file can include entries such as:

.venv/
__pycache__/
*.py[cod]
.env
.env.*
!.env.example

Add report-file exclusions only if the repository's intended workflow does not require those reports to be tracked.

---

🗺️ Roadmap

Potential future improvements include:

- More consistent device inventory and report schemas.
- Better assessment progress and error reporting.
- Additional automated tests for report generation.
- Clearer separation between CLI and GUI dependencies.
- Improved graphical display compatibility.
- Better evidence collection and remediation tracking.
- Exportable, privacy-conscious assessment summaries.
- Documentation of supported camera protocols and tested environments.
- Reproducible dependency management.

These are proposed improvements, not claims that the features are already implemented.

---

📄 License

Confirm the project's actual license before distributing or modifying it.

If the repository uses the MIT License, include the corresponding "LICENSE" file and update the badge accordingly.

Do not claim a specific license until it has been verified.

---

🤝 Contributing

Contributions that improve reliability, maintainability, documentation, usability, and defensive security are welcome.

Before submitting a change:

1. Explain the problem or improvement.
2. Keep changes focused.
3. Test the affected functionality.
4. Document new dependencies and configuration.
5. Avoid committing credentials or sensitive assessment data.
6. Include appropriate tests where practical.

---

📚 Documentation

Start with the command-line help:

python cctv_assessment.py --help

Review the Python source code and existing report files for implementation-specific details.

Documented capabilities should be verified against the current source and tested behavior.

---

<p align="center">
  <strong>CCTV Security Assessment Suite</strong><br>
  Authorized Testing · Defensive Security · Responsible Disclosure
</p>
