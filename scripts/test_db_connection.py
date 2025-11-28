
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load env
env_file = project_root / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()

# Override DATABASE_URL for local execution
# db_url = os.environ.get("DATABASE_URL", "")
# if "@db:5432" in db_url:
#     print("Adjusting DATABASE_URL for local execution (db -> localhost)")
#     os.environ["DATABASE_URL"] = db_url.replace("@db:5432", "@localhost:5432")

from app.core.database import db_manager

async def test_connection():
    print(f"Testing connection to: {os.environ.get('DATABASE_URL')}")
    try:
        await db_manager.initialize()
        async with db_manager.get_sql_session() as session:
            result = await session.execute(text("SELECT 1"))
            print(f"Connection successful! Result: {result.scalar()}")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_connection())
