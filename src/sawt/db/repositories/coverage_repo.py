"""Coverage area repository for database operations."""

from typing import Any

from sawt.db.connection import get_connection


class CoverageRepository:
    """Repository for delivery coverage area operations."""

    @staticmethod
    async def get_area_by_id(area_id: int) -> dict[str, Any] | None:
        """Get a coverage area by ID."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, name_ar, name_en, city, aliases_ar, is_active
                FROM covered_areas
                WHERE id = $1 AND is_active = true
                """,
                area_id,
            )
            return dict(row) if row else None

    @staticmethod
    async def get_all_active_areas() -> list[dict[str, Any]]:
        """Get all active coverage areas."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name_ar, name_en, city, aliases_ar
                FROM covered_areas
                WHERE is_active = true
                ORDER BY name_ar
                """
            )
            return [dict(row) for row in rows]

    @staticmethod
    async def find_area_by_name(name: str) -> dict[str, Any] | None:
        """Find a coverage area by exact name match."""
        async with get_connection() as conn:
            # Try exact match first
            row = await conn.fetchrow(
                """
                SELECT id, name_ar, name_en, city, aliases_ar
                FROM covered_areas
                WHERE is_active = true
                  AND (name_ar = $1 OR name_en = $1)
                """,
                name,
            )
            if row:
                return dict(row)

            # Try alias match
            row = await conn.fetchrow(
                """
                SELECT id, name_ar, name_en, city, aliases_ar
                FROM covered_areas
                WHERE is_active = true
                  AND $1 = ANY(aliases_ar)
                """,
                name,
            )
            return dict(row) if row else None

    @staticmethod
    async def search_area(search_term: str) -> list[dict[str, Any]]:
        """Search for coverage areas by partial name match."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name_ar, name_en, city, aliases_ar
                FROM covered_areas
                WHERE is_active = true
                  AND (
                    name_ar ILIKE $1
                    OR name_en ILIKE $1
                    OR EXISTS (
                      SELECT 1 FROM unnest(aliases_ar) alias
                      WHERE alias ILIKE $1
                    )
                  )
                ORDER BY name_ar
                LIMIT 5
                """,
                f"%{search_term}%",
            )
            return [dict(row) for row in rows]

    @staticmethod
    async def check_coverage(area_name: str) -> tuple[bool, dict[str, Any] | None]:
        """
        Check if an area is covered for delivery.
        Returns (is_covered, area_info).
        """
        # Clean the area name
        area_name = area_name.strip()

        # Try exact match first
        area = await CoverageRepository.find_area_by_name(area_name)
        if area:
            return True, area

        # Try fuzzy search
        suggestions = await CoverageRepository.search_area(area_name)
        if suggestions:
            # Return the first match as a suggestion but not as covered
            return False, {"suggestions": suggestions}

        return False, None

    @staticmethod
    async def get_areas_by_city(city: str) -> list[dict[str, Any]]:
        """Get all coverage areas in a specific city."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name_ar, name_en, city, aliases_ar
                FROM covered_areas
                WHERE is_active = true AND city = $1
                ORDER BY name_ar
                """,
                city,
            )
            return [dict(row) for row in rows]
