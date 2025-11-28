
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import select, delete
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load env
env_file = project_root / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()

from app.core.database import db_manager
from app.models import User

async def test_write():
    print("Testing database write operation...")
    try:
        await db_manager.initialize()
        
        test_email = f"test_write_{uuid4()}@example.com"
        
        async with db_manager.get_sql_session() as session:
            # Create
            print(f"Creating test user: {test_email}")
            new_user = User(
                email=test_email,
                name="Test Write User",
                hashed_password="dummy",
                is_active=True
            )
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            user_id = new_user.id
            print(f"User created with ID: {user_id}")
            
            # Read
            print("Verifying user exists...")
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            fetched_user = result.scalar_one_or_none()
            
            if fetched_user and fetched_user.email == test_email:
                print("✅ Write verification successful!")
            else:
                print("❌ Write verification failed: User not found or mismatch")
                sys.exit(1)
                
            # Delete (Cleanup)
            print("Cleaning up...")
            await session.delete(fetched_user)
            await session.commit()
            print("Cleanup complete.")
            
    except Exception as e:
        print(f"❌ Write test failed: {e}")
        sys.exit(1)
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_write())
