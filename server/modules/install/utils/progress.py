# install/utils/progress.py
import sys
from typing import Optional, Generator
from contextlib import contextmanager

class ProgressBar:
    """Handles progress visualization for installation steps."""
    
    def __init__(self, total: int = 100, prefix: str = "", width: int = 50):
        self.total = total
        self.prefix = prefix
        self.width = width
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
        print(f"\r{self.prefix} |{bar}| {percentage}%", end="", file=sys.stderr)
        
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
        self.message = ""
    
    def spin(self, message: str) -> None:
        """Display spinning progress indicator."""
        char = self.chars[self.current % len(self.chars)]
        print(f"\r{char} {message}", end="", file=sys.stderr)
        self.current += 1
        
    @contextmanager
    def task(self, description: str) -> Generator[None, None, None]:
        """Context manager for task progress."""
        print(f"\n{description}...", file=sys.stderr)
        self.message = description
        try:
            yield
            print(f"\r✓ {description}", file=sys.stderr)
        except:
            print(f"\r✗ {description}", file=sys.stderr)
            raise