import os
import time
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import json

# Import the scanner logic (we can just import the function if we modify scanner.py slightly)
# For simplicity, we'll re-implement or call the script.
import scanner

app = FastAPI()

CACHE = {
    "data": None,
    "last_scan": 0
}
CACHE_TTL = 60 # Seconds between scans

# Dashboard Assets
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("index.html", "r") as f:
        return f.read()

@app.get("/api/pulse")
async def get_pulse():
    now = time.time()
    if not CACHE["data"] or (now - CACHE["last_scan"] > CACHE_TTL):
        print("Pulse scanner active...")
        CACHE["data"] = scanner.analyze_workspace()
        CACHE["last_scan"] = now
    return CACHE["data"]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7777)
