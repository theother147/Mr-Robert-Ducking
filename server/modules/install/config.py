# install/config.py
from pathlib import Path
import sys
from typing import Dict, Any
from .exceptions import PlatformError

class InstallerConfig:
    """Configuration settings for the installation process."""
    
    # Base paths
    VENV_DIR = Path(__file__).parent.parent.parent / ".venv" 
    TEMP_DIR = Path(sys.prefix) / "temp"
    
    # Platform specific settings
    PLATFORM_CONFIG: Dict[str, Dict[str, Any]] = {
        "win32": {
            "ollama_url": "https://ollama.ai/download/OllamaSetup.exe",
            "installer_name": "OllamaSetup.exe",
            "install_args": ["/VERYSILENT", "/NORESTART"],
            "python_path": VENV_DIR / "Scripts" / "python.exe"
        },
        "darwin": {
            "ollama_url": "https://ollama.com/download/Ollama-darwin.zip",
            "installer_name": "Ollama-darwin.zip",
            "install_path": Path("/Applications/Ollama.app"),
            "python_path": VENV_DIR / "bin" / "python"
        },
        "linux": {
            "ollama_url": "https://ollama.com/install.sh",
            "python_path": VENV_DIR / "bin" / "python"
        }
    }
    
    # Model settings
    MODEL_CONFIG = {
        "name": "codellama",
        "version": "latest"
    }
    
    # Download settings
    DOWNLOAD_CONFIG = {
        "chunk_size": 8192,
        "timeout": 30,
        "retry_attempts": 3,
        "retry_delay": 1
    }
    
    @classmethod
    def get_platform_config(cls) -> Dict[str, Any]:
        """Get configuration for current platform."""
        if sys.platform not in cls.PLATFORM_CONFIG:
            raise PlatformError(sys.platform)
        return cls.PLATFORM_CONFIG[sys.platform]