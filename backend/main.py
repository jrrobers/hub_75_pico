import os
from fastapi import FastAPI, HTTPException
import psycopg2

app = FastAPI(
    title="Pico W HUB75 DB Proxy",
    description="Exposes PostgreSQL metrics to the Pico W matrix display over a simple HTTP endpoint."
)

# Railway injects the DATABASE_URL environment variable automatically if connected to a Postgres service
DATABASE_URL = os.environ.get("DATABASE_URL")

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "pico-hub75-proxy"}

@app.get("/distinct-keys")
def get_distinct_keys():
    """Queries PostgreSQL to count the distinct number of organizations in the access_keys table."""
    if not DATABASE_URL:
        raise HTTPException(
            status_code=500,
            detail="DATABASE_URL environment variable is missing. Please set it in your Railway dashboard."
        )
    
    try:
        # Establish connection to PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Execute query for distinct organizations
        cursor.execute("SELECT COUNT(DISTINCT organization) FROM access_keys;")
        result = cursor.fetchone()
        
        # Extract count
        count = result[0] if result else 0
        
        # Close connection
        cursor.close()
        conn.close()
        
        return {"count": count}
        
    except Exception as e:
        print("Database error:", e)
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )
