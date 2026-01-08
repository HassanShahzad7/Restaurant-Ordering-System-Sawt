"""Numeral normalization tools for FastMCP."""

from fastmcp import FastMCP

from sawt.utils.numeral_converter import (
    normalize_numerals as convert_numerals,
    extract_phone_number,
    extract_quantity,
)


def register_numeral_tools(mcp: FastMCP) -> None:
    """Register numeral normalization tools with the MCP server."""

    @mcp.tool()
    async def normalize_numerals(text: str) -> dict:
        """
        تحويل الأرقام العربية (٠-٩) إلى أرقام إنجليزية (0-9).

        Args:
            text: النص المراد تحويله

        Returns:
            dict with original_text and normalized_text
        """
        return {
            "original_text": text,
            "normalized_text": convert_numerals(text),
        }

    @mcp.tool()
    async def extract_phone(text: str) -> dict:
        """
        استخراج رقم الجوال السعودي من النص.

        Args:
            text: النص الذي يحتوي على رقم الجوال

        Returns:
            dict with found, phone_number
        """
        phone = extract_phone_number(text)
        return {
            "found": phone is not None,
            "phone_number": phone,
            "original_text": text,
        }

    @mcp.tool()
    async def extract_qty(text: str) -> dict:
        """
        استخراج الكمية من النص.

        Args:
            text: النص الذي يحتوي على الكمية

        Returns:
            dict with found, quantity
        """
        qty = extract_quantity(text)
        return {
            "found": qty is not None,
            "quantity": qty,
            "original_text": text,
        }
