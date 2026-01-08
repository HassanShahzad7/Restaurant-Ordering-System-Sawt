"""Tests for numeral converter utilities."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sawt.utils.numeral_converter import (
    normalize_numerals,
    extract_phone_number,
    extract_quantity,
)


class TestNormalizeNumerals:
    """Tests for normalize_numerals function."""

    def test_arabic_to_english(self):
        """Test converting Arabic-Indic numerals."""
        assert normalize_numerals("٠١٢٣٤٥٦٧٨٩") == "0123456789"

    def test_mixed_numerals(self):
        """Test mixed Arabic and English numerals."""
        assert normalize_numerals("05٥١234٥٦٧") == "0551234567"

    def test_no_numerals(self):
        """Test text without numerals."""
        assert normalize_numerals("مرحبا") == "مرحبا"

    def test_phone_number(self):
        """Test normalizing phone number."""
        assert normalize_numerals("٠٥٥١٢٣٤٥٦٧") == "0551234567"


class TestExtractPhoneNumber:
    """Tests for extract_phone_number function."""

    def test_local_format(self):
        """Test extracting local format phone number."""
        assert extract_phone_number("رقمي 0551234567") == "0551234567"

    def test_arabic_numerals(self):
        """Test extracting phone with Arabic numerals."""
        assert extract_phone_number("٠٥٥١٢٣٤٥٦٧") == "0551234567"

    def test_international_format(self):
        """Test extracting international format."""
        assert extract_phone_number("+966551234567") == "0551234567"

    def test_no_phone(self):
        """Test when no phone number present."""
        assert extract_phone_number("مرحبا") is None


class TestExtractQuantity:
    """Tests for extract_quantity function."""

    def test_arabic_quantity(self):
        """Test extracting Arabic numeral quantity."""
        assert extract_quantity("أبي ٣ برجر") == 3

    def test_english_quantity(self):
        """Test extracting English numeral quantity."""
        assert extract_quantity("أبي 5 برجر") == 5

    def test_no_quantity(self):
        """Test when no quantity present."""
        assert extract_quantity("أبي برجر") is None
