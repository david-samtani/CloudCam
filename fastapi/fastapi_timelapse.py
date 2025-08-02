import os
import subprocess

def stitch_timelapse(in_dir, out_name, out_dir):
    """
    Builds a timelapse video from all .jpg frames in `in_dir`, using a glob
    pattern so filenames don’t have to be strictly numeric, and ensures
    the output dimensions are even for H.264.
    """
    video_out_path = os.path.join(out_dir, f"{out_name}.mp4")

    cmd = [
        "ffmpeg",
        "-y",                        # overwrite without asking
        "-framerate", "30",          # frames per second
        "-pattern_type", "glob",     # allow *.jpg wildcard
        "-i", os.path.join(in_dir, "*.jpg"),
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",  # make width & height even
        "-c:v", "libx264",           # H.264 codec
        "-pix_fmt", "yuv420p",       # broad compatibility
        video_out_path
    ]

    subprocess.run(cmd, check=True)
    print(f"Timelapse video '{video_out_path}' created successfully!")
