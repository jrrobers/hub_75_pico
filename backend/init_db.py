# init_db.py
"""Utility script to create a SQLite test database with sample data for the backend.
Run with: `python init_db.py` after installing the backend dependencies.
"""
import os
import asyncio
from sqlalchemy import Table, Column, String, MetaData, insert
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

metadata = MetaData()
access_keys = Table(
    "access_keys",
    metadata,
    Column("id", String, primary_key=True),
    Column("organization", String),
)

async def main():
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
        # Insert sample rows
        sample = [
            {"id": "1", "organization": "Acme Corp"},
            {"id": "2", "organization": "Beta Ltd"},
            {"id": "3", "organization": "Acme Corp"},
        ]
        await conn.execute(insert(access_keys), sample)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
