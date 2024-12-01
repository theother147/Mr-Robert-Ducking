# install/core/model.py
from typing import Optional, Dict, Any
from ..config import InstallerConfig
from ..exceptions import ModelError
from ..utils.progress import SpinnerProgress
from .venv import VenvManager  # Add this import

class ModelManager:
    """Manages AI model installation and verification."""
    
    def __init__(self, venv_manager: VenvManager):
        self.config = InstallerConfig.MODEL_CONFIG
        self.spinner = SpinnerProgress()
        self.venv = venv_manager
        
    def verify_model(self) -> bool:
        """Check if model is already installed."""
        try:
            import ollama
            client = ollama.Client()
            models = client.list()
            return any(
                model["name"] == self.config["name"] 
                for model in models["models"]
            )
        except ImportError:
            raise ModelError(
                self.config["name"],
                "Ollama package not installed. Please ensure virtual environment is set up correctly."
            )
        except Exception:
            return False
            
    def pull_model(self) -> None:
        """Download and install the model."""
        try:
            import ollama
            with self.spinner.task(f"Pulling {self.config['name']} model"):
                client = ollama.Client()
                client.pull(
                    self.config["name"],
                    stream=True
                )
        except ImportError:
            raise ModelError(
                self.config["name"],
                "Ollama package not installed"
            )
        except Exception as e:
            raise ModelError(
                self.config["name"],
                f"Failed to pull model: {str(e)}"
            )

    def install(self) -> None:
        """Install model if not present."""
        try:
            # Run model installation in venv context
            args = [
                str(self.venv.get_python_path()),
                "-c",
                "import ollama; client = ollama.Client(); client.pull('codellama')"
            ]
            self.venv.run_in_venv(args)
        except Exception as e:
            raise ModelError(self.config["name"], str(e))