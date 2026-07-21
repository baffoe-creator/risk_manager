"""OCR parsing and extraction logic."""
import logging
import re
import cv2
import numpy as np
import pytesseract
from typing import Optional, Dict, Any
from src.models.risk_engine import TradeState

logger = logging.getLogger(__name__)


class OCRParser:
    """Parses OCR text into structured data."""
    
    def __init__(self, confidence_threshold: float = 50.0):
        self.confidence_threshold = confidence_threshold
        self.region_mappings = {
            "pnl": {"key": "current_pnl", "type": "float"},
            "position_size": {"key": "position_size", "type": "float"},
            "trade_count": {"key": "num_trades", "type": "int"},
            "trading_time": {"key": "trading_time_minutes", "type": "int"},
            "consecutive_losses": {"key": "consecutive_losses", "type": "int"}
        }
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Apply threshold to get binary image
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Invert if needed (white text on dark background)
            # Check if most pixels are dark (background is dark)
            if np.mean(binary) < 128:
                binary = cv2.bitwise_not(binary)
            
            # Denoise
            denoised = cv2.medianBlur(binary, 1)
            
            return denoised
            
        except Exception as e:
            logger.error(f"Failed to preprocess image: {e}")
            return image
    
    def extract_text(self, image: np.ndarray, region_name: str) -> Optional[str]:
        """Extract text from an image region."""
        try:
            # Preprocess
            processed = self.preprocess_image(image)
            
            # Configure Tesseract
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.-$'
            
            # Extract text
            text = pytesseract.image_to_string(
                processed, 
                config=custom_config,
                lang='eng'
            )
            
            # Clean up
            text = text.strip()
            
            if not text:
                logger.debug(f"No text extracted from region '{region_name}'")
                return None
            
            logger.debug(f"Extracted text from '{region_name}': '{text}'")
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract text from '{region_name}': {e}")
            return None
    
    def parse_value(self, text: str, value_type: str) -> Optional[Any]:
        """Parse text to the appropriate value type."""
        if not text:
            return None
        
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[$,]', '', text)
            
            # Extract first number found
            if value_type == "float":
                match = re.search(r'[-+]?\d*\.?\d+', cleaned)
                if match:
                    return float(match.group())
            elif value_type == "int":
                match = re.search(r'[-+]?\d+', cleaned)
                if match:
                    return int(match.group())
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to parse value '{text}' as {value_type}: {e}")
            return None
    
    def parse_region(self, image: np.ndarray, region_name: str) -> Optional[Any]:
        """Parse a single region and return the extracted value."""
        if region_name not in self.region_mappings:
            logger.error(f"Unknown region: {region_name}")
            return None
        
        mapping = self.region_mappings[region_name]
        
        # Extract text
        text = self.extract_text(image, region_name)
        if text is None:
            return None
        
        # Parse value
        value = self.parse_value(text, mapping["type"])
        
        return value
    
    def parse_to_trade_state(self, region_images: Dict[str, np.ndarray]) -> Optional[TradeState]:
        """Parse multiple regions into a TradeState object."""
        try:
            extracted = {}
            
            # Parse each region
            for region_name, image in region_images.items():
                if region_name in self.region_mappings:
                    value = self.parse_region(image, region_name)
                    if value is not None:
                        key = self.region_mappings[region_name]["key"]
                        extracted[key] = value
                        logger.debug(f"Parsed '{region_name}': {value}")
            
            # Check if we have all required fields
            required_keys = ["current_pnl", "position_size", "num_trades", 
                           "trading_time_minutes", "consecutive_losses"]
            
            missing = [k for k in required_keys if k not in extracted]
            if missing:
                logger.warning(f"Missing required fields: {missing}")
                return None
            
            # Create TradeState
            state = TradeState(
                current_pnl=float(extracted["current_pnl"]),
                position_size=float(extracted["position_size"]),
                num_trades=int(extracted["num_trades"]),
                trading_time_minutes=int(extracted["trading_time_minutes"]),
                consecutive_losses=int(extracted["consecutive_losses"])
            )
            
            logger.debug(f"Created TradeState from OCR: {state}")
            return state
            
        except Exception as e:
            logger.error(f"Failed to parse to TradeState: {e}")
            return None
    
    def validate_confidence(self, text: str) -> bool:
        """Validate OCR confidence based on text quality."""
        if not text:
            return False
        
        # Check for gibberish
        if len(text) < 2:
            return False
        
        # Check for valid characters
        if not re.search(r'\d', text):
            return False
        
        return True