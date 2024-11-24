import subprocess
import sys
import os
import time
from pathlib import Path
from typing import Tuple

def create_and_activate_venv() -> str:
    """Create virtual environment and return path to python executable"""
    import venv
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("Creating virtual environment...")
        venv.create(venv_path, with_pip=True)
    
    if sys.platform == "win32":
        python_executable = venv_path / "Scripts" / "python.exe"
    else:
        python_executable = venv_path / "bin" / "python"
    return str(python_executable)

def install_requirements(python_executable):
    from tqdm import tqdm  # Import after bootstrap
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        print("requirements.txt not found.")
        return False

    total_modules = len(requirements)
    print("\nInstalling Python modules...")
    print()  # Add newline for progress bar
    
    with tqdm(total=total_modules, desc="Installing modules", unit="module") as pbar:
        for requirement in requirements:
            try:
                module_name = requirement.split('==')[0].split('>=')[0].split('<=')[0].strip()

                # Check if module is already installed
                check_result = subprocess.run(
                    [python_executable, '-m', 'pip', 'show', module_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                if check_result.returncode == 0:
                    pbar.set_description(f"Already installed: {module_name}")
                    pbar.update(1)
                    continue

                # Install module
                pbar.set_description(f"Installing {requirement}")
                install_result = subprocess.run(
                    [python_executable, '-m', 'pip', 'install', requirement],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                if install_result.returncode != 0:
                    print(f"\nFailed to install {requirement}")
                    return False
                    
                pbar.update(1)
                
            except Exception as e:
                print(f"\nError installing {requirement}: {e}")
                return False
    
    print("\n✓ All Python modules installed successfully")
    return True

def download_with_progress(url: str, output_path: Path) -> bool:
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))

        with open(output_path, 'wb') as file, tqdm(
            desc="Downloading Ollama",
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                pbar.update(size)
        return True
    except Exception as e:
        print(f"\nDownload failed: {e}")
        return False

def is_ollama_installed() -> Tuple[bool, str]:
    """
    Check if Ollama is installed by running 'ollama --version'.
    
    Returns:
        Tuple[bool, str]: A tuple containing:
            - Boolean indicating if Ollama is installed
            - String with version information or error message
    """
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            shell=False
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, f"Ollama {version}"
        else:
            return False, "Ollama is not installed or not in PATH"
            
    except FileNotFoundError:
        return False, "Ollama is not installed or not in PATH"
    except Exception as e:
        return False, f"Error checking Ollama installation: {str(e)}"

def install_ollama() -> bool:
    print("Checking Ollama installation...")
    is_installed, message = is_ollama_installed()
    
    if is_installed:
        print(f"✓ Ollama is already installed: {message}")
        return check_and_install_model()  # Continue with model installation

    print("Installing Ollama...")

    if sys.platform == "win32":
        temp_dir = Path(os.getenv('TEMP', '/tmp'))
        installer_path = temp_dir / "OllamaSetup.exe"
        download_url = "https://ollama.ai/download/OllamaSetup.exe"

        try:
            print() # Add newline before progress bar
            if not download_with_progress(download_url, installer_path):
                return False

            print("\nRunning installer...")
            print() # Add newline before progress bar
            with tqdm(total=1, desc="Installing") as pbar:
                subprocess.run([str(installer_path), '/VERYSILENT', '/NORESTART'], check=True)
                pbar.update(1)

            print("\nWaiting for installation to complete...")
            time.sleep(5)

            is_installed, message = is_ollama_installed()
            
            if is_installed:
                print(f"✓ Ollama installed: {message}")
                return check_and_install_model()  # Continue with model installation
            else:
                print("Please restart your terminal to complete Ollama installation.")
                return False
        except Exception as e:
            print(f"Failed to install Ollama: {e}")
            return False
        finally:
            if installer_path.exists():
                installer_path.unlink()
                
    elif sys.platform.startswith('linux'):
        try:
            print("Installing Ollama using official install script...")
            print() # Add newline before progress bar
            
            with tqdm(total=1, desc="Installing") as pbar:
                # Run curl install script
                process = subprocess.Popen(
                    "curl -fsSL https://ollama.com/install.sh | sh",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                _, stderr = process.communicate()
                
                if process.returncode != 0:
                    print(f"Installation failed: {stderr.decode()}")
                    return False
                    
                pbar.update(1)

            # Verify installation
            is_installed, message = is_ollama_installed()
            if is_installed:
                print(f"\n✓ Ollama installed: {message}")
                return check_and_install_model()  # Continue with model installation
            else:
                print("\nInstallation may have failed or PATH needs to be updated")
                print("Please try starting a new terminal session")
                return False

        except Exception as e:
            print(f"\nFailed to install Ollama: {e}")
            return False
    else:
        print(f"Unsupported platform: {sys.platform}")
        return False

def install_bootstrap_dependencies(python_executable: str) -> bool:
    """Install the minimal dependencies needed for the installer to run."""
    print("Installing essential dependencies...")
    
    bootstrap_modules = [
        "tqdm",
        "requests"
    ]

    try:
        for module in bootstrap_modules:
            print(f"Installing {module}...")
            subprocess.check_call(
                [python_executable, "-m", "pip", "install", module],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        return True
    except Exception as e:
        print(f"Failed to install essential dependencies: {e}")
        return False

def check_and_install_model() -> bool:
    """Check if codellama model is installed, download if not."""
    try:
        import ollama

        print("\nChecking for required AI model...")
        client = ollama.Client()
        
        try:
            # Get list of installed models
            models = client.list()
            
            # Extract model names from ListResponse
            if hasattr(models, 'models'):
                model_names = [model.model.split(':')[0] for model in models.models]
            else:
                print(f"Unexpected model list format: {type(models)}")
                model_names = []
            
            # Check if model exists before showing download message
            if 'codellama' in model_names:
                print("✓ CodeLlama model already installed")
                return True
            
            # Only show download messages if model needs to be installed    
            print("\nDownloading CodeLlama model...")
            print("This may take a while depending on your internet connection...")
            print()  # Add newline before progress indicator
            
            from tqdm import tqdm
            with tqdm(desc="Downloading model") as pbar:
                client.pull('codellama')
                pbar.update(1)
            
            print("\n✓ CodeLlama model installed successfully")
            return True
            
        except AttributeError as ae:
            print(f"\nError accessing model attributes: {ae}")
            print("Response format:", models)
            return False
            
    except Exception as e:
        print(f"\nFailed to install CodeLlama model: {e}")
        return False

def main():
    # First create venv and get its python executable
    python_executable = create_and_activate_venv()
    
    # Install bootstrap dependencies into venv
    if not install_bootstrap_dependencies(python_executable):
        print("Failed to install essential dependencies. Aborting.")
        return False
        
    # Now install remaining requirements
    if not install_requirements(python_executable):
        sys.exit(1)

    if not install_ollama():
        sys.exit(1)

if __name__ == "__main__":
    main()