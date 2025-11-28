#!/usr/bin/env python3
"""
Reset user mastery data for testing.

This script clears all mastery records for a specific user,
allowing them to start fresh with the recommendation system.

Usage:
    # Reset by user email
    uv run python scripts/reset_user_mastery.py --email test@example.com

    # Reset by user ID
    uv run python scripts/reset_user_mastery.py --user-id f84bcc2c-ea90-48a3-8ad9-479302bbbdbf

    # Reset for a specific graph only
    uv run python scripts/reset_user_mastery.py --email test@example.com --graph-id 79f6869b-a9d1-4965-b864-dafd6a3faa6d
"""

import asyncio
import argparse
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import DatabaseManager
from app.core.config import Settings
from app.models.user import User, UserMastery


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Get user by email."""
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    """Get user by ID."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def count_mastery_records(db: AsyncSession, user_id: UUID, graph_id: UUID | None = None) -> int:
    """Count mastery records for a user."""
    from sqlalchemy import func
    stmt = select(func.count(UserMastery.node_id)).where(UserMastery.user_id == user_id)
    if graph_id:
        stmt = stmt.where(UserMastery.graph_id == graph_id)
    result = await db.execute(stmt)
    return result.scalar() or 0


async def delete_mastery_records(db: AsyncSession, user_id: UUID, graph_id: UUID | None = None) -> int:
    """Delete mastery records for a user. Returns count of deleted records."""
    stmt = delete(UserMastery).where(UserMastery.user_id == user_id)
    if graph_id:
        stmt = stmt.where(UserMastery.graph_id == graph_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


async def main():
    parser = argparse.ArgumentParser(description="Reset user mastery data")
    parser.add_argument("--email", type=str, help="User email address")
    parser.add_argument("--user-id", type=str, help="User UUID")
    parser.add_argument("--graph-id", type=str, help="Optional: Reset only for this graph")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")

    args = parser.parse_args()

    if not args.email and not args.user_id:
        parser.error("Either --email or --user-id is required")

    # Initialize database
    settings = Settings()
    db_manager = DatabaseManager(settings)
    await db_manager.initialize()

    async with db_manager.get_session() as db:
        # Find the user
        if args.email:
            user = await get_user_by_email(db, args.email)
            if not user:
                print(f"❌ User with email '{args.email}' not found")
                return
        else:
            try:
                user_id = UUID(args.user_id)
            except ValueError:
                print(f"❌ Invalid UUID format: {args.user_id}")
                return
            user = await get_user_by_id(db, user_id)
            if not user:
                print(f"❌ User with ID '{args.user_id}' not found")
                return

        print(f"📧 User: {user.email} (ID: {user.id})")

        # Parse graph_id if provided
        graph_id = None
        if args.graph_id:
            try:
                graph_id = UUID(args.graph_id)
                print(f"📊 Graph: {graph_id}")
            except ValueError:
                print(f"❌ Invalid graph UUID format: {args.graph_id}")
                return

        # Count existing records
        count = await count_mastery_records(db, user.id, graph_id)
        print(f"📝 Found {count} mastery records")

        if count == 0:
            print("✅ No mastery records to delete")
            return

        if args.dry_run:
            print(f"🔍 Dry run: Would delete {count} mastery records")
            return

        # Confirm deletion
        confirm = input(f"⚠️  Delete {count} mastery records? [y/N]: ")
        if confirm.lower() != 'y':
            print("❌ Cancelled")
            return

        # Delete records
        deleted = await delete_mastery_records(db, user.id, graph_id)
        print(f"✅ Deleted {deleted} mastery records")
        print("🎉 User can now start fresh with the recommendation system!")

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
