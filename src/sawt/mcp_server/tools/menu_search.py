"""Menu search tools for FastMCP."""

from typing import Any

from fastmcp import FastMCP

from sawt.db.repositories.menu_repo import MenuRepository


def register_menu_tools(mcp: FastMCP) -> None:
    """Register menu search tools with the MCP server."""

    @mcp.tool()
    async def menu_vector_search(
        query: str,
        limit: int = 5,
        category: str | None = None,
    ) -> dict:
        """
        البحث في قائمة الطعام باستخدام البحث الدلالي.
        يستخدم Pinecone للبحث المتجهي، مع fallback للبحث النصي.

        Args:
            query: نص البحث (مثال: "برجر دجاج", "شي حار")
            limit: عدد النتائج المطلوبة (افتراضي: 5)
            category: تصفية حسب الفئة (اختياري)

        Returns:
            dict with items list containing search results
        """
        # Import here to avoid circular imports
        try:
            from sawt.vector.pinecone_client import search_menu_items

            # Try vector search first
            results = await search_menu_items(query, top_k=limit, category=category)
            if results:
                return {
                    "found": True,
                    "count": len(results),
                    "items": results,
                    "search_type": "vector",
                }
        except Exception:
            # Fall back to text search if vector search fails
            pass

        # Fallback to simple text search
        if category:
            items = await MenuRepository.get_items_by_category(category)
            # Filter by query
            items = [
                i for i in items
                if query.lower() in i["name_ar"].lower()
                or (i.get("description_ar") and query.lower() in i["description_ar"].lower())
            ][:limit]
        else:
            items = await MenuRepository.search_items(query, limit=limit)

        return {
            "found": len(items) > 0,
            "count": len(items),
            "items": [
                {
                    "id": i["id"],
                    "name_ar": i["name_ar"],
                    "description_ar": i.get("description_ar", ""),
                    "price": float(i["price"]),
                    "category_ar": i["category_ar"],
                    "is_combo": i.get("is_combo", False),
                }
                for i in items
            ],
            "search_type": "text",
        }

    @mcp.tool()
    async def get_menu_item(item_id: int) -> dict:
        """
        الحصول على تفاصيل صنف من القائمة.

        Args:
            item_id: رقم الصنف

        Returns:
            dict with item details
        """
        item = await MenuRepository.get_item_by_id(item_id)

        if not item:
            return {
                "found": False,
                "message_ar": "الصنف غير موجود",
            }

        return {
            "found": True,
            "item": {
                "id": item["id"],
                "name_ar": item["name_ar"],
                "name_en": item.get("name_en"),
                "description_ar": item.get("description_ar", ""),
                "price": float(item["price"]),
                "category_ar": item["category_ar"],
                "is_combo": item.get("is_combo", False),
                "preparation_time_mins": item.get("preparation_time_mins", 15),
            },
        }

    @mcp.tool()
    async def get_item_modifiers(item_id: int) -> dict:
        """
        الحصول على الإضافات والتعديلات المتاحة لصنف.

        Args:
            item_id: رقم الصنف

        Returns:
            dict with modifier groups and options
        """
        item = await MenuRepository.get_item_with_modifiers(item_id)

        if not item:
            return {
                "found": False,
                "message_ar": "الصنف غير موجود",
            }

        modifier_groups = []
        for group in item.get("modifier_groups", []):
            modifier_groups.append({
                "group_id": group["id"],
                "name_ar": group["name_ar"],
                "selection_type": group["selection_type"],
                "is_required": group["is_required"],
                "min_selections": group["min_selections"],
                "max_selections": group["max_selections"],
                "modifiers": [
                    {
                        "id": m["id"],
                        "name_ar": m["name_ar"],
                        "price_adjustment": float(m["price_adjustment"]),
                    }
                    for m in group.get("modifiers", [])
                ],
            })

        return {
            "found": True,
            "item_id": item_id,
            "item_name_ar": item["name_ar"],
            "has_modifiers": len(modifier_groups) > 0,
            "modifier_groups": modifier_groups,
        }

    @mcp.tool()
    async def get_menu_categories() -> dict:
        """
        الحصول على قائمة الفئات المتاحة.

        Returns:
            dict with categories list
        """
        categories = await MenuRepository.get_all_categories()
        return {
            "count": len(categories),
            "categories": categories,
        }

    @mcp.tool()
    async def get_items_by_category(category_ar: str) -> dict:
        """
        الحصول على جميع الأصناف في فئة معينة.

        Args:
            category_ar: اسم الفئة بالعربية

        Returns:
            dict with items in the category
        """
        items = await MenuRepository.get_items_by_category(category_ar)

        return {
            "found": len(items) > 0,
            "count": len(items),
            "category": category_ar,
            "items": [
                {
                    "id": i["id"],
                    "name_ar": i["name_ar"],
                    "description_ar": i.get("description_ar", ""),
                    "price": float(i["price"]),
                    "is_combo": i.get("is_combo", False),
                }
                for i in items
            ],
        }
