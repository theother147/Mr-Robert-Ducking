# install/utils/progress.py
import sys
import time
from typing import Optional, Generator
from contextlib import contextmanager

def format_size(size_bytes: int) -> str:
    """Format bytes into human readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:3.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

class ProgressBar:
    """Handles progress visualization for installation steps."""
    
    def __init__(self, total: int = 100, prefix: str = "", width: int = 50, show_size: bool = True):
        self.total = total
        self.prefix = prefix
        self.width = width
        self.show_size = show_size
        self.current = 0
        self.last_printed = -1
    
    def update(self, current: Optional[int] = None) -> None:
        """Update progress bar."""
        if current is not None:
            self.current = min(current, self.total)
        else:
            self.current = min(self.current + 1, self.total)
            
        percentage = int(self.current * 100 / self.total)
        filled = int(self.width * self.current / self.total)
        bar = "█" * filled + "-" * (self.width - filled)
        
        # Build progress string
        progress_str = f"\r{self.prefix} |{bar}|"
        if self.show_size and self.total > 0:
            current_size = format_size(self.current)
            total_size = format_size(self.total)
            progress_str += f" {current_size}/{total_size}"
        else:
            progress_str += f" {percentage}%"
            
        print(progress_str, end="", file=sys.stderr)
        
        if self.current >= self.total:
            print(file=sys.stderr)
    
    @contextmanager
    def task(self, description: str):
        """Context manager for task progress."""
        print(f"\n{description}...", file=sys.stderr)
        try:
            yield self
        finally:
            if self.current < self.total:
                self.current = self.total
                self.update()

class SpinnerProgress:
    """Simple spinner for indeterminate progress."""
    
    def __init__(self):
        self.chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.current = 0
        self.active = False
    
    def _spin(self) -> None:
        """Update spinner animation."""
        while self.active:
            char = self.chars[self.current % len(self.chars)]
            print(f"\r{char} {self.message}", end="", file=sys.stderr)
            self.current += 1
            time.sleep(0.1)
    
    @contextmanager
    def task(self, description: str) -> Generator[None, None, None]:
        """Context manager for task progress."""
        self.message = description
        print("", file=sys.stderr)  # New line before task
        self.active = True
        try:
            yield
            self.active = False
            print(f"\r✓ {description}", file=sys.stderr)
        except:
            self.active = False
            print(f"\r✗ {description}", file=sys.stderr)
            raise