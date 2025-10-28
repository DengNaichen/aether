"""Entry point for running the worker as a module."""
import asyncio
from app.worker.worker import main

if __name__ == "__main__":
    asyncio.run(main())
