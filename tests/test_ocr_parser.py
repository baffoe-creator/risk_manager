"""Tests for OCR parser."""
import pytest
import numpy as np
from src.ocr.parser import OCRParser
from src.models.risk_engine import TradeState


class TestOCRParser:
    """Tests for OCRParser."""
    
    @pytest.fixture
    def parser(self):
        """Create an OCR parser instance."""
        return OCRParser()
    
    def test_parse_value_float(self, parser):
        """Test parsing float values."""
        assert parser.parse_value("$1,234.56", "float") == 1234.56
        assert parser.parse_value("-500.00", "float") == -500.0
        assert parser.parse_value("0.01", "float") == 0.01
        assert parser.parse_value("invalid", "float") is None
    
    def test_parse_value_int(self, parser):
        """Test parsing integer values."""
        assert parser.parse_value("42", "int") == 42
        assert parser.parse_value("-10", "int") == -10
        assert parser.parse_value("1,234", "int") == 1234
        assert parser.parse_value("invalid", "int") is None
    
    def test_extract_text_empty(self, parser):
        """Test extracting text from empty image."""
        # Create a blank image
        blank_image = np.zeros((50, 100), dtype=np.uint8)
        text = parser.extract_text(blank_image, "test")
        # Should return None or empty string
        assert text is None or text == ""
    
    def test_parse_region_unknown(self, parser):
        """Test parsing unknown region."""
        image = np.zeros((50, 100), dtype=np.uint8)
        result = parser.parse_region(image, "unknown")
        assert result is None
    
    def test_validate_confidence(self, parser):
        """Test confidence validation."""
        # Valid text
        assert parser.validate_confidence("$1,234.56") is True
        assert parser.validate_confidence("42") is True
        
        # Invalid text
        assert parser.validate_confidence("") is False
        assert parser.validate_confidence("a") is False
    
    def test_preprocess_image(self, parser):
        """Test image preprocessing."""
        # Create a test image
        image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        # Preprocess
        processed = parser.preprocess_image(image)
        
        # Should return a binary image
        assert processed.shape == image.shape
        assert processed.dtype == np.uint8
        
        # Should have only 0 and 255 values
        unique_values = np.unique(processed)
        assert len(unique_values) <= 2
        assert all(v in [0, 255] for v in unique_values)
    
    def test_parse_to_trade_state_missing_fields(self, parser):
        """Test parsing with missing fields."""
        # Create incomplete images dict
        images = {
            "pnl": np.zeros((50, 100), dtype=np.uint8),
            "position_size": np.zeros((50, 100), dtype=np.uint8)
        }
        
        result = parser.parse_to_trade_state(images)
        assert result is None
    
    def test_parse_to_trade_state_empty_images(self, parser):
        """Test parsing with empty images dict."""
        result = parser.parse_to_trade_state({})
        assert result is None