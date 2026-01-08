"""Embedding generation for menu items using Pinecone Inference."""

from pinecone import Pinecone

from sawt.config import get_settings


_pc_client: Pinecone | None = None


def get_pinecone_client() -> Pinecone:
    """Get or create Pinecone client."""
    global _pc_client
    if _pc_client is None:
        settings = get_settings()
        _pc_client = Pinecone(api_key=settings.pinecone_api_key)
    return _pc_client


async def generate_embedding(text: str, input_type: str = "query") -> list[float]:
    """
    Generate embedding for text using Pinecone Inference API.

    Uses llama-text-embed-v2 model (1024 dimensions) to match the index.
    Falls back to a simple hash-based embedding for development.

    Args:
        text: Text to embed
        input_type: "query" for search queries, "passage" for documents/menu items
    """
    settings = get_settings()

    if not settings.pinecone_api_key:
        # Development fallback: simple hash-based embedding
        return _simple_hash_embedding(text, dimension=1024)

    try:
        pc = get_pinecone_client()

        # Use Pinecone's inference API to generate embeddings
        # Use "query" for search queries, "passage" for indexing documents
        embeddings = pc.inference.embed(
            model="llama-text-embed-v2",
            inputs=[text],
            parameters={"input_type": input_type}
        )

        return embeddings[0].values

    except Exception as e:
        print(f"Pinecone embedding error: {e}")
        # Fall back to hash-based embedding
        return _simple_hash_embedding(text, dimension=1024)


def _simple_hash_embedding(text: str, dimension: int = 1024) -> list[float]:
    """
    Generate a simple hash-based embedding for development/testing.

    This is NOT suitable for production - use only for development.
    """
    import hashlib

    # Create a deterministic embedding from text hash
    text_bytes = text.encode("utf-8")
    hash_bytes = hashlib.sha512(text_bytes).digest()

    # Extend to desired dimension
    embedding = []
    for i in range(dimension):
        # Use modulo to cycle through hash bytes
        byte_val = hash_bytes[i % len(hash_bytes)]
        # Normalize to [-1, 1]
        normalized = (byte_val / 255.0) * 2 - 1
        embedding.append(normalized)

    # Normalize the vector
    norm = sum(x * x for x in embedding) ** 0.5
    if norm > 0:
        embedding = [x / norm for x in embedding]

    return embedding


def prepare_menu_item_text(item: dict) -> str:
    """
    Prepare menu item text for embedding.

    Combines name, description, and category into a single text.
    """
    parts = []

    if item.get("name_ar"):
        parts.append(item["name_ar"])

    if item.get("description_ar"):
        parts.append(item["description_ar"])

    if item.get("category_ar"):
        parts.append(f"فئة: {item['category_ar']}")

    if item.get("is_combo"):
        parts.append("كومبو")

    return " ".join(parts)
