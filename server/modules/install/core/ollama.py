# install/core/ollama.py
import sys
import os
import time
import subprocess
import threading
from pathlib import Path
from typing import Tuple

from ..config import InstallerConfig
from ..utils.progress import SpinnerProgress

class OllamaManager:
    """Manages Ollama installation and verification."""
    
    def __init__(self):
        self.config = InstallerConfig.get_platform_config()
        self.spinner = SpinnerProgress()
        
    def verify_installation(self) -> Tuple[bool, str]:
        """Verify Ollama installation."""
        try:
            with self.spinner.task("Verifying Ollama installation"):
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
            
    def _run_with_spinner(self, description: str, func, *args, **kwargs):
        """Run a function with a spinner animation"""
        result = None
        error = None
        
        def worker():
            nonlocal result, error
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                error = e
        
        thread = threading.Thread(target=worker)
        
        with self.spinner.task(description):
            thread.start()
            thread.join()
            
        if error:
            raise error
        return result
            
    def _install_windows(self) -> None:
        """Windows-specific installation."""
        # Import Downloader here to avoid early import
        from ..utils.download import Downloader
        
        temp_dir = InstallerConfig.TEMP_DIR
        installer_path = temp_dir / self.config["installer_name"]
        
        try:
            # Download installer
            downloader = Downloader()
            downloader.download(
                self.config["ollama_url"],
                installer_path
            )
            
            print("\nInstalling Ollama (this may take a few minutes)...")
            
            # Run installer with progress indication
            def run_installer():
                subprocess.run(
                    [str(installer_path)] + self.config["install_args"],
                    check=True,
                    capture_output=True
                )
            
            self._run_with_spinner(
                "Installing Ollama",
                run_installer
            )
            
            # Wait for service with progress indication
            def wait_service():
                time.sleep(5)  # Give the service time to start
                
            self._run_with_spinner(
                "Waiting for Ollama service to start",
                wait_service
            )
            
        finally:
            if installer_path.exists():
                installer_path.unlink()
                
    def _install_mac(self) -> None:
        """macOS-specific installation."""
        # Import Downloader here to avoid early import
        from ..utils.download import Downloader
        
        temp_dir = InstallerConfig.TEMP_DIR
        zip_path = temp_dir / self.config["installer_name"]
        
        try:
            # Download and extract
            downloader = Downloader()
            downloader.download(
                self.config["ollama_url"],
                zip_path
            )
            
            print("\nInstalling Ollama (this may take a few minutes)...")
            
            def install_app():
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
            
            self._run_with_spinner(
                "Installing Ollama application",
                install_app
            )
            
            self._run_with_spinner(
                "Waiting for Ollama service to start",
                time.sleep,
                5
            )
            
        finally:
            if zip_path.exists():
                zip_path.unlink()
                
    def _install_linux(self) -> None:
        """Linux-specific installation."""
        print("\nInstalling Ollama (this may take a few minutes)...")
        
        def run_install():
            process = subprocess.run(
                "curl -fsSL https://ollama.com/install.sh | sh",
                shell=True,
                capture_output=True,
                text=True
            )
            if process.returncode != 0:
                raise RuntimeError(f"Installation failed: {process.stderr}")
        
        self._run_with_spinner(
            "Installing Ollama",
            run_install
        )
            
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
                raise RuntimeError(f"Unsupported platform: {sys.platform}")
                
            # Verify installation
            is_installed, message = self.verify_installation()
            if not is_installed:
                raise RuntimeError(f"Installation verification failed: {message}")
                
        except Exception as e:
            raise RuntimeError(f"Installation failed: {str(e)}")