"""Screen capture functionality for OCR."""
import logging
import time
from typing import Optional, Tuple, Dict, Any
from PIL import ImageGrab
import numpy as np

logger = logging.getLogger(__name__)


class ScreenCapture:
    """Handles screen capture for OCR regions."""
    
    def __init__(self):
        self.regions: Dict[str, Tuple[int, int, int, int]] = {}
        self.window_title: Optional[str] = None
    
    def set_region(self, name: str, x: int, y: int, width: int, height: int):
        """Set a region of interest for capture."""
        self.regions[name] = (x, y, width, height)
        logger.debug(f"Region '{name}' set: ({x}, {y}, {width}x{height})")
    
    def set_window(self, title: str):
        """Set the window title to capture from."""
        self.window_title = title
        logger.debug(f"Window title set: {title}")
    
    def capture_region(self, name: str) -> Optional[np.ndarray]:
        """Capture a specific region as a numpy array."""
        if name not in self.regions:
            logger.error(f"Region '{name}' not configured")
            return None
        
        try:
            x, y, width, height = self.regions[name]
            
            # Capture the region
            screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            
            # Convert to numpy array for OpenCV processing
            import numpy as np
            img_array = np.array(screenshot)
            
            return img_array
            
        except Exception as e:
            logger.error(f"Failed to capture region '{name}': {e}")
            return None
    
    def capture_all_regions(self) -> Dict[str, np.ndarray]:
        """Capture all configured regions."""
        results = {}
        for name in self.regions:
            img = self.capture_region(name)
            if img is not None:
                results[name] = img
        return results
    
    def get_region_positions(self) -> Dict[str, Tuple[int, int, int, int]]:
        """Get all configured region positions."""
        return self.regions.copy()