"""Script to index menu items to Pinecone."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sawt.db.connection import init_db, close_db
from sawt.vector.menu_indexer import index_all_menu_items


async def main():
    """Index all menu items to Pinecone."""
    print("Indexing menu items to Pinecone...")

    await init_db()

    try:
        result = await index_all_menu_items()
        print(f"\n{result['message']}")

    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
