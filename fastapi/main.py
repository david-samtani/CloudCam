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
TMP_FILE_NAME = "requested_overlay_movie_tmp"
TMP_FILE = f"/data/cloudcams/cloudcam2025/{TMP_FILE_NAME}.mp4"

def run_job(req: OverlayRequest):
    # delete any old movie
    try:
        os.remove(OUTPUT_FILE)
    except FileNotFoundError:
        pass
    # 1) generate all the frames + movie
    timelapse_with_overlay(
        movie_out_name = TMP_FILE_NAME, 
        constellations = req.constellations, 
        stars = req.stars, 
        planets = req.planets, 
        date_of_timelapse = req.date
    )

    # atomically move into place
    os.replace(TMP_FILE, OUTPUT_FILE)

    return {"status": "completed"}

@app.post("/generate-overlay/")
async def generate_overlay(req: OverlayRequest, bg: BackgroundTasks):
    # kick off the long‑running job in background
    bg.add_task(run_job, req)
    return {"status": "started"}
