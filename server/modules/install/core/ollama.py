# install/core/ollama.py
import sys
import os
import time
import subprocess
from pathlib import Path
from typing import Tuple

from ..config import InstallerConfig
from ..exceptions import OllamaError
from ..utils.progress import SpinnerProgress
from ..utils.download import Downloader

class OllamaManager:
    """Manages Ollama installation and verification."""
    
    def __init__(self):
        self.config = InstallerConfig.get_platform_config()
        self.spinner = SpinnerProgress()
        self.downloader = Downloader()
        
    def verify_installation(self) -> Tuple[bool, str]:
        """Verify Ollama installation."""
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return True, f"Ollama {result.stdout.strip()}"
            return False, "Ollama is not responding"
            
        except FileNotFoundError:
            return False, "Ollama not found in PATH"
        except Exception as e:
            return False, str(e)
            
    def _install_windows(self) -> None:
        """Windows-specific installation."""
        temp_dir = Path(os.getenv('TEMP', '/tmp'))
        installer_path = temp_dir / self.config["installer_name"]
        
        try:
            # Download installer
            with self.spinner.task("Downloading Ollama"):
                self.downloader.download(
                    self.config["ollama_url"],
                    installer_path
                )
            
            # Run installer
            with self.spinner.task("Installing Ollama"):
                subprocess.run(
                    [str(installer_path)] + self.config["install_args"],
                    check=True
                )
                
            # Wait for service
            time.sleep(5)
            
        finally:
            if installer_path.exists():
                installer_path.unlink()
                
    def _install_mac(self) -> None:
        """macOS-specific installation."""
        temp_dir = Path(os.getenv('TMPDIR', '/tmp'))
        zip_path = temp_dir / self.config["installer_name"]
        
        try:
            # Download and extract
            with self.spinner.task("Downloading Ollama"):
                self.downloader.download(
                    self.config["ollama_url"],
                    zip_path
                )
                
            with self.spinner.task("Installing Ollama"):
                subprocess.run([
                    "unzip", "-q", str(zip_path),
                    "-d", "/Applications"
                ], check=True)
                
                subprocess.run([
                    "xattr", "-dr",
                    "com.apple.quarantine",
                    "/Applications/Ollama.app"
                ], check=True)
                
                subprocess.run([
                    "open", "/Applications/Ollama.app"
                ], check=True)
                
            time.sleep(5)
            
        finally:
            if zip_path.exists():
                zip_path.unlink()
                
    def _install_linux(self) -> None:
        """Linux-specific installation."""
        with self.spinner.task("Installing Ollama"):
            process = subprocess.run(
                "curl -fsSL https://ollama.com/install.sh | sh",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if process.returncode != 0:
                raise OllamaError(f"Installation failed: {process.stderr}")
                
    def install(self) -> None:
        """Install Ollama for current platform."""
        is_installed, message = self.verify_installation()
        if is_installed:
            return
            
        try:
            if sys.platform == "win32":
                self._install_windows()
            elif sys.platform == "darwin":
                self._install_mac()
            elif sys.platform.startswith('linux'):
                self._install_linux()
            else:
                raise OllamaError(f"Unsupported platform", sys.platform)
                
            # Verify installation
            is_installed, message = self.verify_installation()
            if not is_installed:
                raise OllamaError("Installation verification failed", message)
                
        except Exception as e:
            raise OllamaError("Installation failed", str(e))