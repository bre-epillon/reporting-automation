import pandas as pd
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Global variable to hold our data
data_cache = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs ONCE when the server starts
    print("Loading CSV into cache...")
    df = pd.read_csv("inputs/premiums_2026-02-27.csv")
    data_cache["df"] = df
    yield
    # This code runs when the server shuts down
    data_cache.clear()


app = FastAPI(lifespan=lifespan)


@app.get("/data")
async def get_data():
    # Return the cached data as JSON
    df = data_cache.get("df")
    if df is not None:
        return df.to_dict(orient="records")
    return {"error": "Data not loaded"}


@app.get("/data/summary")
async def get_summary():
    # Example of processing the cached data
    df = data_cache.get("df")
    if df is not None:
        return {"rows": len(df), "columns": list(df.columns)}
    return {"error": "No data"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
