"""
One-command build script.
Run: python build.py
Output: dist/MissionTracker.exe
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onefile",
    "--windowed",
    "--name", "MissionTracker",
    "--add-data", f"{ROOT / 'app'}:app",
    "--hidden-import", "PySide6.QtXml",
    "--hidden-import", "pandas._libs.tslibs.np_datetime",
    "--hidden-import", "pandas._libs.tslibs.nattype",
    "--hidden-import", "pandas._libs.tslibs.timedeltas",
    str(ROOT / "app" / "main.py"),
]

print("Building MissionTracker.exe …")
result = subprocess.run(cmd, cwd=ROOT)
if result.returncode == 0:
    print("\n✓ Build complete: dist/MissionTracker.exe")
else:
    print("\n✗ Build failed. Check output above.")
    sys.exit(result.returncode)
