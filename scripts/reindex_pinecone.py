"""Re-index menu items from database to Pinecone."""

import asyncio
import sys
import io

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import psycopg2
from sawt.config import get_settings
from sawt.vector.pinecone_client import batch_upsert_menu_items


def main():
    settings = get_settings()

    # Get menu items from database
    print("Connecting to database...")
    conn = psycopg2.connect(settings.database_url)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name_ar, name_en, description_ar, category_ar, price, is_combo, is_available
        FROM menu_items
        WHERE is_available = TRUE
    ''')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"Found {len(rows)} menu items in database")

    # Convert to dict format
    items = []
    for row in rows:
        items.append({
            'id': row[0],
            'name_ar': row[1],
            'name_en': row[2],
            'description_ar': row[3],
            'category_ar': row[4],
            'price': float(row[5]),
            'is_combo': row[6],
            'is_available': row[7],
        })

    # Index to Pinecone
    print("Indexing to Pinecone (this may take a minute)...")
    count = asyncio.run(batch_upsert_menu_items(items))
    print(f"Successfully indexed {count} items to Pinecone!")


if __name__ == "__main__":
    main()
