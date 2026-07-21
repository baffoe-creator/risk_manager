"""OCR threading implementation."""
import logging
import threading
import queue
import time
from typing import Optional, Dict, Any
from src.ocr.capture import ScreenCapture
from src.ocr.parser import OCRParser
from src.models.risk_engine import TradeState

logger = logging.getLogger(__name__)


class OCRCaptureThread(threading.Thread):
    """Thread for capturing and parsing OCR data."""
    
    def __init__(self, capture_interval: float = 1.0):
        super().__init__()
        self.capture_interval = capture_interval
        self.running = False
        self.daemon = True
        
        self.capture = ScreenCapture()
        self.parser = OCRParser()
        
        self.result_queue: queue.Queue = queue.Queue()
        
        self.regions_configured = False
    
    def configure_regions(self, regions: Dict[str, tuple]):
        """Configure capture regions."""
        for name, (x, y, width, height) in regions.items():
            self.capture.set_region(name, x, y, width, height)
        self.regions_configured = True
        logger.info(f"Configured {len(regions)} OCR regions")
    
    def run(self):
        """Main thread loop."""
        self.running = True
        logger.info("OCR capture thread started")
        
        while self.running:
            try:
                if not self.regions_configured:
                    time.sleep(0.5)
                    continue
                
                # Capture all regions
                images = self.capture.capture_all_regions()
                
                if not images:
                    logger.warning("No images captured")
                    time.sleep(0.1)
                    continue
                
                # Parse to TradeState
                state = self.parser.parse_to_trade_state(images)
                
                if state is not None:
                    # Success - push result
                    self.result_queue.put({
                        "success": True,
                        "state": state,
                        "timestamp": time.time()
                    })
                    logger.debug("OCR capture successful")
                else:
                    # Failure - push sentinel
                    self.result_queue.put({
                        "success": False,
                        "error": "Failed to parse OCR data",
                        "timestamp": time.time()
                    })
                    logger.debug("OCR capture failed")
                
                # Wait for next capture
                time.sleep(self.capture_interval)
                
            except Exception as e:
                logger.error(f"OCR thread error: {e}")
                self.result_queue.put({
                    "success": False,
                    "error": str(e),
                    "timestamp": time.time()
                })
                time.sleep(1.0)
        
        logger.info("OCR capture thread stopped")
    
    def stop(self):
        """Stop the OCR thread."""
        self.running = False
        logger.info("Stopping OCR capture thread")
    
    def get_result(self, block: bool = False, timeout: float = None) -> Optional[Dict]:
        """Get the latest OCR result from the queue."""
        try:
            if block:
                return self.result_queue.get(timeout=timeout)
            else:
                return self.result_queue.get_nowait()
        except queue.Empty:
            return None
    
    def clear_queue(self):
        """Clear the result queue."""
        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
            except queue.Empty:
                break
        logger.debug("OCR result queue cleared")