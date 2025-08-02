import os
import fastapi_astrometry
from fastapi_timelapse import stitch_timelapse

def timelapse_with_overlay(movie_out_name, constellations: str, stars: str, planets: str, date_of_timelapse: str):
    image_in_dir = f'/data/cloudcams/cloudcam2025/{date_of_timelapse}_movie'
    image_out_dir = '/home/akami-3/gitlabsource/CloudCams/requested_overlay_images'
    movie_out_dir = '/data/cloudcams/cloudcam2025'

    for img_name in os.listdir(image_in_dir):
        img_path = os.path.join(image_in_dir, img_name)
        fastapi_astrometry.overlay(img_path, image_out_dir, constellations, stars, planets)


    stitch_timelapse(image_out_dir, movie_out_name, movie_out_dir)
