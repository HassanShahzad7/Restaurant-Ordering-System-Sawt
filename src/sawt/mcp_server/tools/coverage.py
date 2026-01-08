"""Coverage area tools for FastMCP."""

from fastmcp import FastMCP

from sawt.db.repositories.coverage_repo import CoverageRepository
from sawt.utils.arabic_utils import normalize_area_name


def register_coverage_tools(mcp: FastMCP) -> None:
    """Register coverage area tools with the MCP server."""

    @mcp.tool()
    async def coverage_check(area_name: str) -> dict:
        """
        التحقق من تغطية منطقة التوصيل.

        Args:
            area_name: اسم المنطقة أو الحي

        Returns:
            dict with is_covered, area_info, suggestions
        """
        # Normalize the area name
        normalized = normalize_area_name(area_name)

        # Check coverage
        is_covered, result = await CoverageRepository.check_coverage(normalized)

        if is_covered and result:
            return {
                "is_covered": True,
                "area_id": result["id"],
                "area_name_ar": result["name_ar"],
                "area_name_en": result.get("name_en"),
                "city": result.get("city", "Riyadh"),
                "message_ar": f"نعم، نوصل لمنطقة {result['name_ar']}",
            }
        elif result and "suggestions" in result:
            suggestions = result["suggestions"]
            suggestion_names = [s["name_ar"] for s in suggestions[:3]]
            return {
                "is_covered": False,
                "suggestions": suggestions[:3],
                "message_ar": f"لم نجد '{area_name}'. هل تقصد: {', '.join(suggestion_names)}؟",
            }
        else:
            return {
                "is_covered": False,
                "suggestions": [],
                "message_ar": f"للأسف لا نغطي منطقة '{area_name}' حالياً. يمكنك الاستلام من الفرع.",
            }

    @mcp.tool()
    async def get_covered_areas() -> dict:
        """
        الحصول على قائمة المناطق المغطاة للتوصيل.

        Returns:
            dict with areas list
        """
        areas = await CoverageRepository.get_all_active_areas()
        return {
            "count": len(areas),
            "areas": [
                {
                    "id": a["id"],
                    "name_ar": a["name_ar"],
                    "name_en": a.get("name_en"),
                    "city": a.get("city", "Riyadh"),
                }
                for a in areas
            ],
        }

    @mcp.tool()
    async def search_areas(query: str) -> dict:
        """
        البحث عن مناطق بالاسم.

        Args:
            query: كلمة البحث

        Returns:
            dict with matching areas
        """
        areas = await CoverageRepository.search_area(query)
        return {
            "count": len(areas),
            "areas": [
                {
                    "id": a["id"],
                    "name_ar": a["name_ar"],
                    "name_en": a.get("name_en"),
                }
                for a in areas
            ],
        }
