"""
Launch script for the Streamlit application.

Usage (PowerShell):
    python main.py

This will run streamlit run app/app.py using the current Python interpreter.
If you prefer to run Streamlit directly, use:
    streamlit run app/app.py

The script attempts to be friendly to virtual environments by using
sys.executable as the Python interpreter.
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
APP_PATH = ROOT / "app" / "app.py"

if not APP_PATH.exists():
    print(f"Streamlit app not found at {APP_PATH}")
    sys.exit(1)

def main():
    python = sys.executable
    cmd = [python, "-m", "streamlit", "run", str(APP_PATH)]

    print("Starting Streamlit app...")
    print("Command:", " ".join(cmd))
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print("Streamlit exited with non-zero status:", e.returncode)
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
