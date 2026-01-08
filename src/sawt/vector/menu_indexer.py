"""Menu indexer for Pinecone."""

import asyncio
from typing import Any

from sawt.db.connection import init_db, close_db, get_connection
from sawt.vector.pinecone_client import batch_upsert_menu_items, upsert_menu_item


async def get_all_menu_items() -> list[dict[str, Any]]:
    """Fetch all menu items from the database."""
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT id, name_ar, name_en, description_ar, description_en,
                   category_ar, category_en, price, is_combo, is_available
            FROM menu_items
            WHERE is_available = true
            """
        )
        return [dict(row) for row in rows]


async def index_all_menu_items() -> dict[str, Any]:
    """
    Index all menu items to Pinecone.

    Returns summary of indexing operation.
    """
    items = await get_all_menu_items()

    if not items:
        return {
            "success": True,
            "total_items": 0,
            "indexed_count": 0,
            "message": "No menu items to index",
        }

    indexed_count = await batch_upsert_menu_items(items)

    return {
        "success": True,
        "total_items": len(items),
        "indexed_count": indexed_count,
        "message": f"Successfully indexed {indexed_count} of {len(items)} menu items",
    }


async def index_single_item(item_id: int) -> dict[str, Any]:
    """
    Index a single menu item to Pinecone.

    Args:
        item_id: ID of the menu item to index

    Returns:
        Status of indexing operation
    """
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, name_ar, name_en, description_ar, description_en,
                   category_ar, category_en, price, is_combo, is_available
            FROM menu_items
            WHERE id = $1
            """,
            item_id,
        )

        if not row:
            return {
                "success": False,
                "message": f"Menu item {item_id} not found",
            }

        item = dict(row)
        success = await upsert_menu_item(item)

        return {
            "success": success,
            "item_id": item_id,
            "item_name": item["name_ar"],
            "message": "Indexed successfully" if success else "Indexing failed",
        }


async def main():
    """Main function for running indexer as a script."""
    print("Starting menu indexer...")

    # Initialize database
    await init_db()

    try:
        result = await index_all_menu_items()
        print(f"Indexing complete: {result}")
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
