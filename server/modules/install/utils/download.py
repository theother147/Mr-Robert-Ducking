# install/utils/download.py
import requests
import subprocess
import json
from pathlib import Path
import time
from typing import Optional, Union, Dict, Any
import os
import sys
import logging
from ..config import InstallerConfig
from .progress import ProgressBar

# Configure logging to suppress debug messages
logging.getLogger('httpx').setLevel(logging.WARNING)

class Downloader:
    """Utility class for downloading files with progress tracking and retries."""
    
    def __init__(self):
        self.config = InstallerConfig.DOWNLOAD_CONFIG
        
    def _download_http(self, url: str, destination: Path) -> None:
        """Download a file using HTTP with progress tracking"""
        attempts = 0
        while attempts < self.config["retry_attempts"]:
            try:
                response = requests.get(
                    url,
                    stream=True,
                    timeout=self.config["timeout"]
                )
                response.raise_for_status()
                
                # Get total size if available
                total_size = int(response.headers.get('content-length', 0))
                
                # Create progress bar
                progress = ProgressBar(
                    total=total_size,
                    prefix=f"pulling {destination.name}...",
                    width=40,
                    show_size=True
                )
                
                # Download with progress tracking
                with open(destination, 'wb') as f:
                    if total_size == 0:
                        f.write(response.content)
                    else:
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=self.config["chunk_size"]):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                progress.update(downloaded)
                                
                return
                
            except Exception as e:
                attempts += 1
                if attempts == self.config["retry_attempts"]:
                    raise RuntimeError(f"Failed to download after {attempts} attempts: {str(e)}")
                time.sleep(self.config["retry_delay"])
                
    def _download_ollama_model(self, model_name: str) -> None:
        """Download an Ollama model with progress tracking"""
        try:
            import ollama
            
            # Initialize progress tracking
            current_file = None
            progress_bar = None
            
            # Pull model and process the stream
            client = ollama.Client()
            for response in client.pull(model_name, stream=True):
                if not isinstance(response, dict):
                    continue
                    
                status = response.get('status', '')
                
                if status == 'pulling manifest':
                    print("pulling manifest")
                    
                elif status == 'downloading':
                    completed = response.get('completed', 0)
                    total = response.get('total', 0)
                    
                    # Create or update progress bar
                    if progress_bar is None:
                        progress_bar = ProgressBar(
                            total=total,
                            prefix=f"pulling {model_name}...",
                            width=40,
                            show_size=True
                        )
                    
                    # Update progress
                    if progress_bar and total > 0:
                        progress_bar.update(completed)
                        
                elif status == 'verifying sha256 digest':
                    if progress_bar:
                        progress_bar.update(progress_bar.total)  # Complete the bar
                    print("verifying sha256 digest")
                    
                elif status == 'writing manifest':
                    print("writing manifest")
                    
                elif status == 'success':
                    print("success")
            
        except Exception as e:
            raise RuntimeError(f"Failed to pull model: {str(e)}")
    
    def download(self, source: Union[str, Dict[str, Any]], destination: Optional[Path] = None) -> None:
        """
        Download a file or model with progress tracking
        
        Args:
            source: URL string for HTTP download, or dict with {'type': 'model', 'name': 'model_name'}
            destination: Path to save downloaded file (not used for model downloads)
        """
        if isinstance(source, dict):
            if source.get('type') == 'model':
                self._download_ollama_model(source['name'])
            else:
                raise ValueError(f"Unknown download type: {source.get('type')}")
        else:
            if not destination:
                raise ValueError("Destination path required for URL downloads")
            self._download_http(source, destination)