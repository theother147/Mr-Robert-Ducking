# install/exceptions.py
from typing import Optional
from pathlib import Path

class InstallError(Exception):
    """Base exception class for installation errors."""
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(f"{message}" + (f"\nDetails: {details}" if details else ""))

class VenvError(InstallError):
    """Virtual environment related errors."""
    def __init__(self, message: str, path: Optional[Path] = None):
        super().__init__(
            f"Virtual environment error: {message}" + 
            (f" at {path}" if path else "")
        )

class RequirementsError(InstallError):
    """Package installation errors."""
    def __init__(self, package: str, message: str):
        super().__init__(f"Failed to install {package}: {message}")

class OllamaError(InstallError):
    """Ollama related errors."""
    def __init__(self, message: str, platform: Optional[str] = None):
        super().__init__(
            f"Ollama error: {message}" +
            (f" on platform {platform}" if platform else "")
        )

class ModelError(InstallError):
    """Model installation/verification errors."""
    def __init__(self, model: str, message: str):
        super().__init__(f"Model error for {model}: {message}")

class DownloadError(InstallError):
    """Download operation errors."""
    def __init__(self, url: str, message: str):
        self.url = url
        super().__init__(f"Download failed from {url}: {message}")

class PlatformError(InstallError):
    """Platform compatibility errors."""
    def __init__(self, platform: str):
        super().__init__(f"Unsupported platform: {platform}")