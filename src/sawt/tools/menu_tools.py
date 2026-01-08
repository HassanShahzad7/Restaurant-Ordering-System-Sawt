"""Menu-related tools for the ordering agent."""

from langchain_core.tools import tool

from sawt.logging_config import log_tool_call, log_tool_result


# This will be populated from the database/Pinecone
# For now, using in-memory storage that gets loaded from DB
_menu_cache: dict[str, dict] = {}


def load_menu_cache(menu_items: list[dict]) -> None:
    """Load menu items into cache (called at startup)."""
    global _menu_cache
    _menu_cache = {item["id"]: item for item in menu_items}


def get_menu_cache() -> dict[str, dict]:
    """Get the menu cache."""
    return _menu_cache


@tool
def search_menu(query: str, category: str | None = None) -> list[dict]:
    """
    Search the menu for items matching the query.
    Uses semantic search via Pinecone for natural language queries.

    Args:
        query: Search query in Arabic (e.g., "برجر", "شي حار", "دجاج مقلي")
        category: Optional category filter (e.g., "الأطباق الرئيسية", "المشروبات")

    Returns:
        List of matching menu items (max 10), each with:
        - id: Item ID
        - name_ar: Arabic name
        - name_en: English name
        - price: Price in SAR
        - category: Category name
        - description_ar: Arabic description
    """
    log_tool_call("search_menu", {"query": query, "category": category})

    # Try Pinecone search first
    try:
        from sawt.vector.pinecone_client import search_menu_items
        import asyncio

        # Run async search synchronously
        loop = asyncio.new_event_loop()
        results = loop.run_until_complete(
            search_menu_items(query, top_k=10, category=category)
        )
        loop.close()

        if results:
            # Log actual items found for debugging
            items_summary = [{"id": r["id"], "name": r["name_ar"], "price": r["price"]} for r in results[:5]]
            log_tool_result("search_menu", {"count": len(results), "source": "pinecone", "items": items_summary})
            return results
    except Exception as e:
        print(f"Pinecone search error in tool: {e}")
        # Fallback to cache search
        pass

    # Fallback: simple text search in cache
    results = []
    query_lower = query.lower()

    for item in _menu_cache.values():
        # Check if query matches name or description
        name_match = query_lower in item.get("name_ar", "").lower() or query_lower in item.get("name_en", "").lower()
        desc_match = query_lower in item.get("description_ar", "").lower()
        cat_match = category is None or category in item.get("category", "")

        if (name_match or desc_match) and cat_match:
            results.append({
                "id": item["id"],
                "name_ar": item["name_ar"],
                "name_en": item.get("name_en", ""),
                "price": item["price"],
                "category": item.get("category", ""),
                "description_ar": item.get("description_ar", ""),
            })

        if len(results) >= 10:
            break

    log_tool_result("search_menu", {"count": len(results), "source": "cache"})
    return results


@tool
def get_item_details(item_id: str) -> dict:
    """
    Get full details for a specific menu item.

    Args:
        item_id: The unique item ID

    Returns:
        Dictionary with full item details:
        - id: Item ID
        - name_ar: Arabic name
        - name_en: English name
        - price: Price in SAR
        - category: Category name
        - description_ar: Arabic description
        - available: Whether item is available
        - modifiers: Available modifications/add-ons
    """
    log_tool_call("get_item_details", {"item_id": item_id})

    if item_id in _menu_cache:
        item = _menu_cache[item_id]
        result = {
            "id": item["id"],
            "name_ar": item["name_ar"],
            "name_en": item.get("name_en", ""),
            "price": item["price"],
            "category": item.get("category", ""),
            "description_ar": item.get("description_ar", ""),
            "available": item.get("available", True),
            "modifiers": item.get("modifiers", []),
        }
        log_tool_result("get_item_details", {"found": True})
        return result

    result = {
        "error": True,
        "message_ar": f"الصنف غير موجود: {item_id}"
    }
    log_tool_result("get_item_details", {"found": False})
    return result


@tool
def get_menu_categories() -> list[str]:
    """
    Get all available menu categories.

    Returns:
        List of category names in Arabic
    """
    log_tool_call("get_menu_categories", {})

    categories = set()
    for item in _menu_cache.values():
        if "category" in item:
            categories.add(item["category"])

    result = sorted(list(categories))
    log_tool_result("get_menu_categories", {"count": len(result)})
    return result
