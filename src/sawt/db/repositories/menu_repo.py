"""Menu repository for database operations."""

from decimal import Decimal
from typing import Any

import asyncpg

from sawt.db.connection import get_connection


class MenuRepository:
    """Repository for menu-related database operations."""

    @staticmethod
    async def get_item_by_id(item_id: int) -> dict[str, Any] | None:
        """Get a menu item by ID."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, name_ar, name_en, description_ar, description_en,
                       category_ar, category_en, price, image_url, is_combo,
                       is_available, preparation_time_mins
                FROM menu_items
                WHERE id = $1 AND is_available = true
                """,
                item_id,
            )
            return dict(row) if row else None

    @staticmethod
    async def get_item_with_modifiers(item_id: int) -> dict[str, Any] | None:
        """Get a menu item with all its modifier groups and options."""
        async with get_connection() as conn:
            # Get the item
            item = await conn.fetchrow(
                """
                SELECT id, name_ar, name_en, description_ar, description_en,
                       category_ar, category_en, price, image_url, is_combo,
                       is_available, preparation_time_mins
                FROM menu_items
                WHERE id = $1 AND is_available = true
                """,
                item_id,
            )
            if not item:
                return None

            result = dict(item)

            # Get modifier groups for this item
            groups = await conn.fetch(
                """
                SELECT mg.id, mg.name_ar, mg.name_en, mg.selection_type,
                       mg.min_selections, mg.max_selections, mg.is_required
                FROM modifier_groups mg
                INNER JOIN item_modifier_groups img ON mg.id = img.modifier_group_id
                WHERE img.menu_item_id = $1
                """,
                item_id,
            )

            modifier_groups = []
            for group in groups:
                group_dict = dict(group)
                # Get modifiers for this group
                modifiers = await conn.fetch(
                    """
                    SELECT id, name_ar, name_en, price_adjustment, is_available
                    FROM modifiers
                    WHERE group_id = $1 AND is_available = true
                    """,
                    group["id"],
                )
                group_dict["modifiers"] = [dict(m) for m in modifiers]
                modifier_groups.append(group_dict)

            result["modifier_groups"] = modifier_groups
            return result

    @staticmethod
    async def get_items_by_ids(item_ids: list[int]) -> list[dict[str, Any]]:
        """Get multiple menu items by IDs."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name_ar, name_en, description_ar, description_en,
                       category_ar, category_en, price, image_url, is_combo,
                       is_available, preparation_time_mins
                FROM menu_items
                WHERE id = ANY($1) AND is_available = true
                """,
                item_ids,
            )
            return [dict(row) for row in rows]

    @staticmethod
    async def get_items_by_category(category_ar: str) -> list[dict[str, Any]]:
        """Get all menu items in a category."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name_ar, name_en, description_ar, description_en,
                       category_ar, category_en, price, image_url, is_combo,
                       is_available, preparation_time_mins
                FROM menu_items
                WHERE category_ar = $1 AND is_available = true
                ORDER BY name_ar
                """,
                category_ar,
            )
            return [dict(row) for row in rows]

    @staticmethod
    async def get_all_categories() -> list[str]:
        """Get all unique menu categories."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT category_ar
                FROM menu_items
                WHERE is_available = true
                ORDER BY category_ar
                """
            )
            return [row["category_ar"] for row in rows]

    @staticmethod
    async def search_items(search_term: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search menu items by name (simple LIKE search)."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name_ar, name_en, description_ar, description_en,
                       category_ar, category_en, price, image_url, is_combo,
                       is_available, preparation_time_mins
                FROM menu_items
                WHERE is_available = true
                  AND (name_ar ILIKE $1 OR name_en ILIKE $1 OR description_ar ILIKE $1)
                LIMIT $2
                """,
                f"%{search_term}%",
                limit,
            )
            return [dict(row) for row in rows]

    @staticmethod
    async def get_modifier_by_id(modifier_id: int) -> dict[str, Any] | None:
        """Get a modifier by ID."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT m.id, m.group_id, m.name_ar, m.name_en, m.price_adjustment,
                       m.is_available, mg.name_ar as group_name_ar
                FROM modifiers m
                INNER JOIN modifier_groups mg ON m.group_id = mg.id
                WHERE m.id = $1
                """,
                modifier_id,
            )
            return dict(row) if row else None

    @staticmethod
    async def get_modifiers_by_ids(modifier_ids: list[int]) -> list[dict[str, Any]]:
        """Get multiple modifiers by IDs."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT m.id, m.group_id, m.name_ar, m.name_en, m.price_adjustment,
                       m.is_available, mg.name_ar as group_name_ar
                FROM modifiers m
                INNER JOIN modifier_groups mg ON m.group_id = mg.id
                WHERE m.id = ANY($1)
                """,
                modifier_ids,
            )
            return [dict(row) for row in rows]

    @staticmethod
    async def validate_modifiers_for_item(
        item_id: int, modifier_ids: list[int]
    ) -> tuple[bool, list[str]]:
        """Validate that modifiers are valid for a given item."""
        errors: list[str] = []

        if not modifier_ids:
            return True, errors

        async with get_connection() as conn:
            # Get valid modifier groups for this item
            valid_groups = await conn.fetch(
                """
                SELECT mg.id, mg.name_ar, mg.is_required, mg.min_selections, mg.max_selections
                FROM modifier_groups mg
                INNER JOIN item_modifier_groups img ON mg.id = img.modifier_group_id
                WHERE img.menu_item_id = $1
                """,
                item_id,
            )
            valid_group_ids = {g["id"] for g in valid_groups}

            # Get the modifiers
            modifiers = await conn.fetch(
                """
                SELECT id, group_id, name_ar, is_available
                FROM modifiers
                WHERE id = ANY($1)
                """,
                modifier_ids,
            )

            # Check each modifier
            for mod in modifiers:
                if mod["group_id"] not in valid_group_ids:
                    errors.append(f"المعدل '{mod['name_ar']}' غير متاح لهذا الصنف")
                if not mod["is_available"]:
                    errors.append(f"المعدل '{mod['name_ar']}' غير متوفر حالياً")

            # Check required groups
            selected_groups: dict[int, int] = {}
            for mod in modifiers:
                group_id = mod["group_id"]
                selected_groups[group_id] = selected_groups.get(group_id, 0) + 1

            for group in valid_groups:
                count = selected_groups.get(group["id"], 0)
                if group["is_required"] and count < group["min_selections"]:
                    errors.append(
                        f"يجب اختيار على الأقل {group['min_selections']} من '{group['name_ar']}'"
                    )
                if count > group["max_selections"]:
                    errors.append(
                        f"لا يمكن اختيار أكثر من {group['max_selections']} من '{group['name_ar']}'"
                    )

        return len(errors) == 0, errors
