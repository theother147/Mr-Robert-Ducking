# install/utils/download.py
from pathlib import Path
import time
from typing import Optional, Callable
import requests
from ..config import InstallerConfig
from ..exceptions import DownloadError
from .progress import ProgressBar

class Downloader:
    """Handles file downloads with progress tracking and retries."""
    
    def download(self, url: str, output_path: Path) -> Path:
        """Download file with progress tracking and retries."""
        config = InstallerConfig.DOWNLOAD_CONFIG
        attempts = 0
        
        while attempts < config["retry_attempts"]:
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                
                progress = ProgressBar(
                    total=total_size,
                    prefix=f"Downloading {output_path.name}"
                )
                
                downloaded = 0
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=config["chunk_size"]):
                        if chunk:
                            downloaded += len(chunk)
                            f.write(chunk)
                            progress.update(downloaded)
                            
                return output_path
                
            except Exception as e:
                attempts += 1
                if attempts >= config["retry_attempts"]:
                    raise DownloadError(url, str(e))
                    
                time.sleep(config["retry_delay"])
                continue