import logging
import asyncio
from src.app.core.database import db_manager

# Configure basic logging
logging.basicConfig(level=logging.INFO)


async def main():
    """
    Initializes and checks all database connections, then closes them.
    """
    logging.info("🚀 Starting database connection check...")
    try:
        # The initialize() method will test all connections in parallel.
        # If any connection fails, it will raise a RuntimeError.
        await db_manager.initialize()
        logging.info("✅ All database connections are working correctly!")
    except Exception as e:
        logging.error(f"🔥 A problem occurred during connection check: {e}")
    finally:
        # Ensure all connections are closed gracefully
        logging.info("🔌 Closing all connections...")
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())