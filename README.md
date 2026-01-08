# Sawt - Arabic Restaurant Ordering Agent

Multi-agent Saudi Arabic dialect chatbot for restaurant ordering using LangGraph, PostgreSQL, and Pinecone.

## Features

- **4 Specialized Agents**: Greeting, Location, Order, Checkout
- **Saudi Arabic Dialect**: Natural conversation in Saudi dialect
- **Semantic Menu Search**: Pinecone vector search for intelligent menu queries
- **101 Menu Items**: Full restaurant menu across 5 categories
- **LangGraph Framework**: Proper multi-agent orchestration with ReAct agents

## Quick Start

```bash
# 1. Start PostgreSQL
docker-compose up -d

# 2. Install dependencies
uv sync

# 3. Create .env file
copy .env.example .env
# Edit .env with your API keys

# 4. Run migrations
uv run alembic upgrade head

# 5. Seed the database
uv run python scripts/seed_menu.py
uv run python scripts/seed_areas.py

# 6. (Optional) Index menu to Pinecone
uv run python scripts/index_menu.py

# 7. Run the chatbot
uv run sawt
```

## Environment Variables

```env
# Required
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_MODEL=openai/gpt-4o-mini

# Database
DATABASE_URL=postgresql://sawt:sawt_password@localhost:5432/sawt

# Optional - Pinecone for semantic search
PINECONE_API_KEY=xxx
PINECONE_INDEX=sawt-menu
```

## Project Structure

```
src/sawt/
├── graph/          # LangGraph workflow and agents
│   ├── state.py    # Agent state definitions
│   └── workflow.py # Multi-agent workflow with ReAct agents
├── tools/          # Agent tools
│   ├── menu_tools.py
│   ├── order_tools.py
│   ├── location_tools.py
│   └── checkout_tools.py
├── vector/         # Pinecone integration
├── db/             # Database layer
└── main.py         # Entry point
```

## Menu Categories

- Main Dishes (35 items): Burgers, Sandwiches, Rice dishes, Grilled
- Appetizers (20 items): Hummus, Salads, Soups, Wings
- Beverages (24 items): Soft drinks, Fresh juices, Smoothies
- Desserts (18 items): Ice cream, Cakes, Arabic sweets
- Sides (16 items): Fries, Nuggets, Rice, Bread

## License

MIT
