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
    """Install requirements from requirements.txt into virtual environment."""
    try:
        with open('requirements.txt', 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        print("requirements.txt not found.")
        return False

    total_modules = len(requirements)
    print("\nInstalling Python modules...")
    print()  # Add newline for progress bar

    success_count = 0
    for requirement in requirements:
        try:
            module_name = requirement.split('==')[0].split('>=')[0].split('<=')[0].strip()
            print(f"Installing {module_name}...")

            # Check if module is already installed
            check_result = subprocess.run(
                [python_executable, '-m', 'pip', 'show', module_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if check_result.returncode == 0:
                print(f"Already installed: {module_name}")
                success_count += 1
                continue

            # Install module
            install_result = subprocess.run(
                [python_executable, '-m', 'pip', 'install', requirement],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if install_result.returncode == 0:
                success_count += 1
            else:
                print(f"Failed to install {requirement}")

        except Exception as e:
            print(f"Error installing {requirement}: {e}")
            return False

    print(f"\n✓ Successfully installed {success_count}/{total_modules} Python modules")
    return True

def download_with_progress(url: str, output_path: Path) -> bool:
    """Download a file with progress indication."""
    try:
        from urllib.request import urlopen
        
        print("Downloading Ollama...")
        with urlopen(url, timeout=30) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            last_percent = 0

            with open(output_path, 'wb') as file:
                while True:
                    chunk = response.read(8192)  # 8KB chunks
                    if not chunk:
                        break
                        
                    size = file.write(chunk)
                    downloaded += size
                    
                    # Update progress every 5%
                    if total_size:
                        percent = int((downloaded / total_size) * 100)
                        if percent >= last_percent + 5:
                            print(f"Progress: {percent}% ({downloaded}/{total_size} bytes)", end='\r')
                            last_percent = percent
                
                print("\nDownload complete!    ")  # Extra spaces to clear previous line
            return True
            
    except Exception as e:
        print(f"\nDownload failed: {e}")
        return False

def is_ollama_installed() -> Tuple[bool, str]:
    """Check if Ollama is installed by running 'ollama --version'."""
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
        return check_and_install_model()

    print("Installing Ollama...")

    if sys.platform == "win32":
        temp_dir = Path(os.getenv('TEMP', '/tmp'))
        installer_path = temp_dir / "OllamaSetup.exe"
        download_url = "https://ollama.ai/download/OllamaSetup.exe"

        try:
            print()  # Add newline before progress bar
            if not download_with_progress(download_url, installer_path):
                return False

            print("\nRunning installer...")
            print()  # Add newline for progress
            print("Installing...", end='', flush=True)
            subprocess.run([str(installer_path), '/VERYSILENT', '/NORESTART'], check=True)
            print(" Done!")

            print("\nWaiting for installation to complete...")
            time.sleep(5)

            is_installed, message = is_ollama_installed()
            if is_installed:
                print(f"✓ Ollama installed: {message}")
                return check_and_install_model()
            else:
                print("Please restart your terminal to complete Ollama installation.")
                return False

        except Exception as e:
            print(f"Failed to install Ollama: {e}")
            return False
        finally:
            if installer_path.exists():
                installer_path.unlink()
                
    elif sys.platform == "darwin":
        try:
            print("Installing Ollama for macOS...")
            download_url = "https://ollama.com/download/Ollama-darwin.zip"
            temp_dir = Path(os.getenv('TMPDIR', '/tmp'))
            zip_path = temp_dir / "Ollama-darwin.zip"
            
            print("\nDownloading Ollama...")
            print()  # Add newline before progress bar
            
            if not download_with_progress(download_url, zip_path):
                return False
                
            print("\nExtracting and installing Ollama.app...")
            print()  # Add newline before progress
            
            print("Installing...", end='', flush=True)
            # Extract .app to Applications
            subprocess.run(["unzip", "-q", str(zip_path), "-d", "/Applications"], check=True)
            
            # Set permissions
            subprocess.run(["xattr", "-dr", "com.apple.quarantine", "/Applications/Ollama.app"], check=True)
            
            # Start Ollama
            subprocess.run(["open", "/Applications/Ollama.app"], check=True)
            print(" Done!")
            
            print("\nWaiting for Ollama service to start...")
            time.sleep(5)  # Give some time for service to initialize
            
            # Verify installation
            is_installed, message = is_ollama_installed()
            if is_installed:
                print(f"\n✓ Ollama installed: {message}")
                return check_and_install_model()
            else:
                print("\nInstallation completed but service not responding")
                print("Please try starting Ollama.app manually")
                return False
                
        except Exception as e:
            print(f"\nFailed to install Ollama: {e}")
            return False
        finally:
            if zip_path.exists():
                zip_path.unlink()
                
    elif sys.platform.startswith('linux'):
        try:
            print("Installing Ollama using official install script...")
            print()  # Add newline before progress bar
            
            print("Installing...", end='', flush=True)
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
                
            print(" Done!")

            # Verify installation
            is_installed, message = is_ollama_installed()
            if is_installed:
                print(f"\n✓ Ollama installed: {message}")
                return check_and_install_model()
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

def check_and_install_model() -> bool:
    """Check if codellama model is installed, download if not."""
    try:
        import server.modules.install.core.ollama as ollama

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
            
            if 'codellama' in model_names:
                print("✓ CodeLlama model already installed")
                return True
            
            print("\nDownloading CodeLlama model...")
            print("This may take a while depending on your internet connection...")
            print()  # Add newline before progress indicator
            
            print("Downloading model... (No progress available)", end='', flush=True)
            client.pull('codellama')
            print(" Done!")
            
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
        
    # Now install remaining requirements
    if not install_requirements(python_executable):
        sys.exit(1)

    if not install_ollama():
        sys.exit(1)

if __name__ == "__main__":
    main()