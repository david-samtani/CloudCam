# main.py
import os
import time
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from timelapse_overlay import timelapse_with_overlay

app = FastAPI()

# allow your web‑page to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # lock down in prod!
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

class OverlayRequest(BaseModel):
    constellations: str
    stars: str
    planets: str
    date: str

# where your script will emit the finished movie:
OUTPUT_FILE = "/data/cloudcams/cloudcam2025/requested_overlay_movie.mp4"

def run_job(req: OverlayRequest):
    # Get the last modification time
    last_mod_time = os.path.getmtime(OUTPUT_FILE)

    # 1) generate all the frames + movie
    timelapse_with_overlay(
        req.constellations, req.stars, req.planets, req.date
    )
    # 2) (optional) wait until the video updates in nas
    while os.path.getmtime(OUTPUT_FILE) != last_mod_time:
        time.sleep(1)

    return {"status": "completed"}

@app.post("/generate-overlay/")
async def generate_overlay(req: OverlayRequest, bg: BackgroundTasks):
    # kick off the long‑running job in background
    bg.add_task(run_job, req)
    return {"status": "started"}
