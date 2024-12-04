# install/core/requirements.py
import subprocess
from pathlib import Path
from typing import List, Tuple
from ..config import InstallerConfig
from ..exceptions import RequirementsError
from ..utils.progress import ProgressBar

class RequirementsManager:
    """Manages Python package installations."""
    
    def __init__(self, python_path: Path):
        self.python_path = python_path
        
    def parse_requirements(self) -> List[str]:
        """Parse requirements from requirements.txt."""
        requirements_path = self.python_path.parent.parent.parent / "requirements.txt"
        try:
            with open(requirements_path, 'r') as f:
                return [
                    line.strip() 
                    for line in f 
                    if line.strip() and not line.startswith('#')
                ]
        except FileNotFoundError:
            raise RequirementsError("requirements.txt", "File not found in server directory")
            
    def install_package(self, package: str) -> bool:
        """Install single package using pip."""
        try:
            result = subprocess.run(
                [
                    str(self.python_path),
                    "-m",
                    "pip",
                    "install",
                    package,
                ],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            raise RequirementsError(package, e.stderr)
            
    def install_all(self) -> None:
        """Install all requirements with progress tracking."""
        requirements = self.parse_requirements()
        progress = ProgressBar(
            total=len(requirements),
            prefix="Installing packages"
        )
        
        for requirement in requirements:
            with progress.task(f"Installing {requirement}"):
                self.install_package(requirement)
                progress.update()