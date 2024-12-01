# install/__main__.py
import sys
from pathlib import Path

from .core.venv import VenvManager
from .core.requirements import RequirementsManager
from .core.ollama import OllamaManager
from .core.model import ModelManager
from .exceptions import InstallError
from .utils.progress import SpinnerProgress

def main() -> int:
    """Run the complete installation process."""
    spinner = SpinnerProgress()
    
    try:
        # Step 1: Setup virtual environment
        with spinner.task("Setting up virtual environment"):
            venv = VenvManager()
            python_path = venv.ensure_venv()
            
        # Step 2: Install Python requirements
        with spinner.task("Installing Python packages"):
            requirements = RequirementsManager(python_path)
            requirements.install_all()
            
        # Step 3: Install Ollama
        with spinner.task("Installing Ollama"):
            ollama = OllamaManager()
            ollama.install()
            
        # Step 4: Install AI model
        with spinner.task("Installing AI model"):
            model = ModelManager(venv)  # Pass venv manager
            model.install()
            
        print("\n✓ Installation completed successfully")
        return 0
        
    except InstallError as e:
        print(f"\n✗ Installation failed: {e.message}")
        if e.details:
            print(f"Details: {e.details}")
        return 1
        
    except KeyboardInterrupt:
        print("\n\n✗ Installation cancelled by user")
        return 1
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())