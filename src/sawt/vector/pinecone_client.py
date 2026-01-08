"""Pinecone client for menu vector search."""

from typing import Any

from pinecone import Pinecone

from sawt.config import get_settings
from sawt.vector.embeddings import generate_embedding, prepare_menu_item_text


_pinecone_client: Pinecone | None = None
_index = None


def get_pinecone_client() -> Pinecone:
    """Get or create Pinecone client."""
    global _pinecone_client
    if _pinecone_client is None:
        settings = get_settings()
        _pinecone_client = Pinecone(api_key=settings.pinecone_api_key)
    return _pinecone_client


def get_index():
    """Get or create Pinecone index reference."""
    global _index
    if _index is None:
        settings = get_settings()
        client = get_pinecone_client()
        _index = client.Index(settings.pinecone_index)
    return _index


async def search_menu_items(
    query: str,
    top_k: int = 10,
    category: str | None = None,
    min_score: float = 0.3,
) -> list[dict[str, Any]]:
    """
    Search menu items using vector similarity.

    Args:
        query: Search query in Arabic
        top_k: Number of results to return
        category: Optional category filter (ignored - semantic search handles this)
        min_score: Minimum similarity score threshold

    Returns:
        List of matching menu items with scores
    """
    settings = get_settings()

    if not settings.pinecone_api_key:
        # No Pinecone configured, return empty
        return []

    try:
        # Generate query embedding with input_type="query" for search
        query_embedding = await generate_embedding(query, input_type="query")

        # Only filter by availability - let semantic search handle category matching
        # Category filters often fail due to exact match requirements
        filter_dict = {"is_available": True}

        # Query Pinecone
        index = get_index()
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict,
        )

        # Format results
        items = []
        for match in results.matches:
            if match.score >= min_score:
                metadata = match.metadata or {}
                items.append({
                    "id": str(match.id),  # Keep as string to match cache
                    "name_ar": metadata.get("name_ar", ""),
                    "name_en": metadata.get("name_en", ""),
                    "description_ar": metadata.get("description_ar", ""),
                    "price": metadata.get("price", 0),
                    "category": metadata.get("category_ar", ""),
                    "category_ar": metadata.get("category_ar", ""),
                    "is_combo": metadata.get("is_combo", False),
                    "score": round(match.score, 3),
                })

        return items

    except Exception as e:
        print(f"Pinecone search error: {e}")
        return []


async def upsert_menu_item(item: dict[str, Any]) -> bool:
    """
    Add or update a menu item in the vector index.

    Args:
        item: Menu item dictionary with id, name_ar, description_ar, etc.

    Returns:
        True if successful
    """
    settings = get_settings()

    if not settings.pinecone_api_key:
        return False

    try:
        # Generate embedding with input_type="passage" for indexing documents
        text = prepare_menu_item_text(item)
        embedding = await generate_embedding(text, input_type="passage")

        # Prepare metadata
        metadata = {
            "name_ar": item.get("name_ar", ""),
            "description_ar": item.get("description_ar", ""),
            "category_ar": item.get("category_ar", ""),
            "price": float(item.get("price", 0)),
            "is_combo": item.get("is_combo", False),
            "is_available": item.get("is_available", True),
        }

        # Upsert to Pinecone
        index = get_index()
        index.upsert(
            vectors=[
                {
                    "id": str(item["id"]),
                    "values": embedding,
                    "metadata": metadata,
                }
            ]
        )

        return True

    except Exception as e:
        print(f"Pinecone upsert error: {e}")
        return False


async def delete_menu_item(item_id: int) -> bool:
    """
    Delete a menu item from the vector index.

    Args:
        item_id: Menu item ID to delete

    Returns:
        True if successful
    """
    settings = get_settings()

    if not settings.pinecone_api_key:
        return False

    try:
        index = get_index()
        index.delete(ids=[str(item_id)])
        return True

    except Exception as e:
        print(f"Pinecone delete error: {e}")
        return False


async def batch_upsert_menu_items(items: list[dict[str, Any]]) -> int:
    """
    Batch upsert menu items to the vector index.

    Args:
        items: List of menu item dictionaries

    Returns:
        Number of successfully indexed items
    """
    settings = get_settings()

    if not settings.pinecone_api_key:
        return 0

    success_count = 0

    try:
        vectors = []

        for item in items:
            text = prepare_menu_item_text(item)
            embedding = await generate_embedding(text, input_type="passage")

            metadata = {
                "name_ar": item.get("name_ar", ""),
                "description_ar": item.get("description_ar", ""),
                "category_ar": item.get("category_ar", ""),
                "price": float(item.get("price", 0)),
                "is_combo": item.get("is_combo", False),
                "is_available": item.get("is_available", True),
            }

            vectors.append({
                "id": str(item["id"]),
                "values": embedding,
                "metadata": metadata,
            })

        # Batch upsert in chunks of 100
        index = get_index()
        batch_size = 100

        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            index.upsert(vectors=batch)
            success_count += len(batch)

        return success_count

    except Exception as e:
        print(f"Pinecone batch upsert error: {e}")
        return success_count
