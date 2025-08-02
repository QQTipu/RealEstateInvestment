import os
import sys
import subprocess

if sys.platform == "win32":
    activate_script = "venv\\Scripts\\activate.bat"
else:
    activate_script = "source venv/bin/activate"

print(f"Pour activer l'environnement : {activate_script}")