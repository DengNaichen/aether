#!/usr/bin/env python3
"""
Run SQL migration scripts against the database.

Usage:
    python scripts/migrations/run_migration.py 001_add_topology_triggers.sql

Or run all migrations:
    python scripts/migrations/run_migration.py --all
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from app.core.database import db_manager


async def run_migration(sql_file: Path):
    """Execute a SQL migration file."""
    print(f"Running migration: {sql_file.name}")

    sql_content = sql_file.read_text()

    async with db_manager.sql_engine.begin() as conn:
        # Execute the entire SQL file
        await conn.execute(text(sql_content))

    print(f"✅ Migration completed: {sql_file.name}")


async def run_all_migrations():
    """Run all SQL migration files in order."""
    migrations_dir = Path(__file__).parent
    sql_files = sorted(migrations_dir.glob("*.sql"))

    if not sql_files:
        print("No migration files found.")
        return

    for sql_file in sql_files:
        await run_migration(sql_file)


async def main():
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file.sql> or --all")
        sys.exit(1)

    await db_manager.initialize()

    try:
        if sys.argv[1] == "--all":
            await run_all_migrations()
        else:
            sql_file = Path(__file__).parent / sys.argv[1]
            if not sql_file.exists():
                print(f"Migration file not found: {sql_file}")
                sys.exit(1)
            await run_migration(sql_file)
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
