# install/utils/download.py
import logging

# Configure root logger first
logging.basicConfig(level=logging.WARNING)

# Disable all debug logging
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).setLevel(logging.WARNING)

import requests
import subprocess
import json
from pathlib import Path
import time
from typing import Optional, Union, Dict, Any
import os
import sys
from ..config import InstallerConfig
from .progress import ProgressBar

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
            progress_bar = None
            last_status = None
            current_digest = None
            
            # Pull model and process the stream
            client = ollama.Client()
            
            try:
                for response in client.pull(model_name, stream=True):
                    # Get attributes from ProgressResponse object
                    status = getattr(response, 'status', '')
                    completed = getattr(response, 'completed', None)
                    total = getattr(response, 'total', None)
                    digest = getattr(response, 'digest', '')
                    
                    # Track new layer downloads
                    if digest and digest != current_digest:
                        if progress_bar:
                            progress_bar.update(progress_bar.total)  # Complete previous bar
                            print()  # New line for next progress bar
                        current_digest = digest
                        progress_bar = None
                    
                    # Show status messages for non-download operations
                    if status and status != last_status and not any(s in status for s in ['pulling']):
                        if progress_bar:
                            print()  # New line after progress bar
                        print(f"{status}...")
                        last_status = status
                        continue
                    
                    # Update progress bar for downloads
                    if total and completed and total > 0 and 'pulling' in status:
                        if progress_bar is None:
                            progress_bar = ProgressBar(
                                total=total,
                                prefix=f"pulling {current_digest[:12] if current_digest else model_name}...",
                                width=40,
                                show_size=True
                            )
                        progress_bar.update(completed)
                
                # If we got here without error, assume success
                if progress_bar:
                    progress_bar.update(progress_bar.total)  # Complete final bar
                    print()
                print("Download completed successfully!")
                return
                    
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("Model already installed!")
                    return
                raise
                
            # Handle error cases
            if progress_bar and progress_bar.current > 0:
                # If we made some progress but didn't complete
                raise RuntimeError("Download started but did not complete. Please try again.")
            else:
                raise RuntimeError("Model download stream ended without success status")
            
        except Exception as e:
            error_msg = str(e)
            if "connection refused" in error_msg.lower():
                error_msg = "Ollama server is not running. Please start Ollama and try again."
            elif "no such file or directory" in error_msg.lower():
                error_msg = "Ollama is not installed or not in PATH. Please install Ollama first."
            raise RuntimeError(f"Failed to pull model: {error_msg}")
    
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