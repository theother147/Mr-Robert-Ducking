import sys
import subprocess
import os
import signal
from pathlib import Path
import shutil
import logging

# Set up basic logging first
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def get_venv_path() -> Path:
    """Get the virtual environment path"""
    return Path(__file__).parent.parent.parent / ".venv"

def is_venv_activated() -> bool:
    """Check if we're running in the correct virtual environment"""
    venv_path = get_venv_path()
    if sys.platform == "win32":
        expected_python = venv_path / "Scripts" / "python.exe"
    else:
        expected_python = venv_path / "bin" / "python"
    
    return Path(sys.executable).resolve() == expected_python.resolve()

def get_venv_pip():
    """Get the path to the virtual environment's pip executable"""
    venv_path = get_venv_path()
    if sys.platform == "win32":
        return venv_path / "Scripts" / "pip.exe"
    return venv_path / "bin" / "pip"

def install_dependencies_in_venv():
    """Install dependencies in the current venv"""
    pip_path = get_venv_pip()
    if not pip_path.exists():
        raise RuntimeError(f"pip not found at {pip_path}")
        
    # Install from requirements.txt
    req_file = Path(__file__).parent.parent.parent / "requirements.txt"
    cmd = [str(pip_path), "install", "-r", str(req_file)]
    
    logger.info("Installing Python dependencies...")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"pip install failed: {result.stderr}")
        
    logger.info("Dependencies installed successfully")

def verify_installation() -> bool:
    """
    Verify virtual environment, packages, and Ollama installation
    Returns True if everything is properly set up, False otherwise
    """
    try:
        # First check and install Python dependencies
        logger.info("Checking virtual environment")
        if not is_venv_activated():
            logger.warning("Not running in virtual environment")
            return False
            
        logger.info("Checking required packages")
        try:
            import colorlog
            import websockets
            import ollama
            import requests
        except ImportError as e:
            logger.warning(f"Missing required package: {e}")
            return False
            
        # Now that dependencies are installed, we can import our modules
        from .utils.progress import SpinnerProgress
        from .core.ollama import OllamaManager
        from modules.config.config import Config
        
        spinner = SpinnerProgress()
            
        # Then check Ollama and model
        if not check_ollama_installed():
            logger.warning("Ollama is not installed")
            return False
            
        if not check_ollama_model():
            logger.warning(f"Ollama model {Config.LLM_MODEL} is not installed")
            return False
            
        return True
            
    except Exception as e:
        logger.error(f"Error verifying installation: {e}")
        return False

def check_ollama_installed() -> bool:
    """Check if Ollama is installed and accessible"""
    try:
        from .core.ollama import OllamaManager
        ollama_manager = OllamaManager()
        is_installed, _ = ollama_manager.verify_installation()
        return is_installed
    except Exception as e:
        logger.error(f"Error checking Ollama: {e}")
        return False

def check_ollama_model() -> bool:
    """Check if the required model is installed"""
    try:
        from .utils.progress import SpinnerProgress
        from modules.config.config import Config
        spinner = SpinnerProgress()
        with spinner.task(f"Checking for model {Config.LLM_MODEL}"):
            result = subprocess.run(['ollama', 'list'], 
                                capture_output=True, 
                                text=True)
            return Config.LLM_MODEL in result.stdout
    except Exception as e:
        logger.error(f"Error checking Ollama model: {e}")
        return False

def install_ollama():
    """Install Ollama using OllamaManager"""
    try:
        from .core.ollama import OllamaManager
        ollama_manager = OllamaManager()
        ollama_manager.install()
    except Exception as e:
        logger.error(f"Failed to install Ollama: {e}")
        raise

def pull_ollama_model():
    """Pull the required Ollama model"""
    try:
        from .utils.download import Downloader
        from modules.config.config import Config
        downloader = Downloader()
        downloader.download({'type': 'model', 'name': Config.LLM_MODEL})
    except Exception as e:
        logger.error(f"Failed to pull Ollama model: {e}")
        raise

def install_dependencies():
    """Install all required dependencies including Ollama"""
    try:
        # First, always handle Python packages
        if not is_venv_activated():
            activate_venv(install_deps=True)
        else:
            install_dependencies_in_venv()
            
        # Now that dependencies are installed, we can import our modules
        from .core.ollama import OllamaManager
        from .utils.progress import SpinnerProgress
        from modules.config.config import Config
        
        # Now verify and install Ollama and model
        if not check_ollama_installed():
            install_ollama()
            
        if not check_ollama_model():
            pull_ollama_model()
            
    except Exception as e:
        logger.error(f"Failed to install dependencies: {e}")
        raise

def activate_venv(install_deps=False):
    """Activate the virtual environment and restart the script"""
    venv_path = get_venv_path()
    
    if not venv_path.exists():
        create_venv_if_needed()

    python_path = get_venv_python()
    if not python_path.exists():
        raise RuntimeError(f"Virtual environment Python not found at {python_path}")

    print("Activating virtual environment...")
    
    # If we need to install dependencies, do it first in the venv
    if install_deps:
        cmd_install = [str(python_path), "-c", 
                      "from modules.install.install import install_dependencies_in_venv; install_dependencies_in_venv()"]
        subprocess.run(cmd_install, check=True)
    
    # Create activation command
    cmd = [str(python_path)] + sys.argv
    shell = sys.platform == "win32"

    try:
        # Start new process with venv Python
        process = subprocess.Popen(cmd, shell=shell)
        
        # Wait for the process to complete or Ctrl+C
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\nStopping server...")
            if sys.platform == "win32":
                # On Windows, create a Ctrl+C event
                process.send_signal(signal.CTRL_C_EVENT)
            else:
                # On Unix, send SIGINT
                process.send_signal(signal.SIGINT)
            # Wait for graceful shutdown
            process.wait()
            print("Server stopped.")
        
        # Exit with the same code as the subprocess
        sys.exit(process.returncode)
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to activate virtual environment: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

def create_venv_if_needed():
    """Create virtual environment if it doesn't exist"""
    venv_path = get_venv_path()
    if not venv_path.exists():
        print("Creating virtual environment...")
        import venv
        venv.create(venv_path, with_pip=True, upgrade_deps=True)

def get_venv_python():
    """Get the path to the virtual environment's Python executable"""
    venv_path = get_venv_path()
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"