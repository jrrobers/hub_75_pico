# backend/app.py
"""FastAPI backend for Hub75 Pico project.
Provides:
- /distinct-organizations: count of distinct organization values in `access_keys` table.
- /stock-prices: latest price for configured stock symbols (using yfinance).
- /random-quote: a random quote from `quotes.txt`.
"""

import os
import random
from typing import Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, Column, String, Table, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import httpx

# Load environment variables (fallbacks provided)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
STOCK_SYMBOLS = os.getenv("STOCK_SYMBOLS", "AAPL,MSFT,GOOG").split(",")
QUOTES_PATH = os.getenv("QUOTES_PATH", "./quotes.txt")

app = FastAPI()

# Setup async SQLAlchemy engine
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
metadata = MetaData()

# Define access_keys table (reflect if exists, otherwise create minimal schema)
access_keys = Table(
    "access_keys",
    metadata,
    Column("id", String, primary_key=True),
    Column("organization", String),
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Ensure tables exist (SQLite case creates table if missing)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

@app.on_event("startup")
async def startup_event():
    await init_db()

# Response models
class OrgCountResponse(BaseModel):
    count: int

class StockPricesResponse(BaseModel):
    prices: Dict[str, float]

class QuoteResponse(BaseModel):
    quote: str

@app.get("/distinct-organizations", response_model=OrgCountResponse)
async def distinct_organizations():
    async with AsyncSessionLocal() as session:
        stmt = select(func.count(func.distinct(access_keys.c.organization)))
        result = await session.execute(stmt)
        count = result.scalar_one()
        return {"count": count}

@app.get("/stock-prices", response_model=StockPricesResponse)
async def stock_prices():
    prices = {}
    try:
        # Build Yahoo Finance API URL with comma‑separated symbols
        symbols_param = ",".join([s.strip() for s in STOCK_SYMBOLS])
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbols_param}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            # Extract price for each symbol
            for item in data.get("quoteResponse", {}).get("result", []):
                sym = item.get("symbol")
                price = item.get("regularMarketPrice")
                if sym and price is not None:
                    prices[sym] = float(price)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"prices": prices}

@app.get("/random-quote", response_model=QuoteResponse)
async def random_quote():
    try:
        with open(QUOTES_PATH, "r", encoding="utf-8") as f:
            quotes = [line.strip() for line in f if line.strip()]
        if not quotes:
            raise HTTPException(status_code=404, detail="No quotes found")
        quote = random.choice(quotes)
        return {"quote": quote}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Quote file not found")
