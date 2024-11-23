import subprocess
import sys
import os
import requests
import time
import venv
from pathlib import Path
import platform
from typing import Tuple
from tqdm import tqdm

def create_and_activate_venv():
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
        return True

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
                return True
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
            install_command = ["curl", "-fsSL", "https://ollama.com/install.sh"]
            shell_command = ["sh"]
            
            # Run curl and pipe to sh
            curl_process = subprocess.Popen(install_command, stdout=subprocess.PIPE)
            shell_process = subprocess.Popen(shell_command, stdin=curl_process.stdout)
            
            # Wait for completion
            curl_process.stdout.close()
            shell_process.communicate()
            
            if shell_process.returncode != 0:
                print("Installation failed")
                return False

            # Verify installation
            is_installed, message = is_ollama_installed()
            if is_installed:
                print(f"✓ Ollama installed: {message}")
                return True
            else:
                print("Installation may have failed or PATH needs to be updated")
                print("Please try starting a new terminal session")
                return False
                
        except Exception as e:
            print(f"Failed to install Ollama: {e}")
            return False
    else:
        print(f"Unsupported platform: {sys.platform}")
        return False

def main():
    python_executable = create_and_activate_venv()
    if not install_requirements(python_executable):
        sys.exit(1)

    if not install_ollama():
        sys.exit(1)

if __name__ == "__main__":
    main()