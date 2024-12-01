# install/core/venv.py
import venv
import subprocess
import os
import sys
from pathlib import Path
from ..config import InstallerConfig
from ..exceptions import VenvError
from ..utils.progress import SpinnerProgress
from typing import List

class VenvManager:
    def __init__(self):
        self.venv_path = InstallerConfig.VENV_DIR
        self.spinner = SpinnerProgress()
        self.requirements_path = self.venv_path.parent / "requirements.txt"

    def get_python_path(self) -> Path:
        """Get path to Python executable in venv."""
        python_path = InstallerConfig.get_platform_config()["python_path"]
        
        if not python_path.exists():
            raise VenvError(
                "Python executable not found",
                str(self.venv_path)
            )
            
        return python_path

    def run_in_venv(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run command in venv context"""
        python_path = self.get_python_path()
        venv_env = {
            **os.environ,
            "VIRTUAL_ENV": str(self.venv_path),
            "PATH": f"{python_path.parent}{os.pathsep}{os.environ['PATH']}"
        }
        return subprocess.run(args, env=venv_env, check=True, capture_output=True)

    def ensure_venv(self) -> Path:
        """Create venv if not exists and install base requirements"""
        if not self.venv_path.exists():
            try:
                venv.create(self.venv_path, with_pip=True)
                # Install base packages first
                self.run_in_venv([str(self.get_python_path()), "-m", "pip", "install", "-U", "pip"])
                self.run_in_venv([str(self.get_python_path()), "-m", "pip", "install", "requests"])
                self.run_in_venv([str(self.get_python_path()), "-m", "pip", "install", "ollama"])
            except Exception as e:
                raise VenvError("Failed to create/setup virtual environment", str(e))
                
        return self.get_python_path()

    def activate(self) -> None:
        """Activate the virtual environment"""
        if not self.venv_path.exists():
            raise VenvError("Virtual environment does not exist")
            
        # Update PATH and VIRTUAL_ENV
        if sys.platform == "win32":
            scripts = self.venv_path / "Scripts"
        else:
            scripts = self.venv_path / "bin"
            
        os.environ["VIRTUAL_ENV"] = str(self.venv_path)
        os.environ["PATH"] = f"{scripts}{os.pathsep}{os.environ['PATH']}"
        sys.prefix = str(self.venv_path)