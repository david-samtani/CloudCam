import cv2
import os
from datetime import datetime, timedelta

def stitch_timelapse(in_dir, out_name, out_dir):
    image_folder = in_dir
    video_name   = out_name
    video_out_path = os.path.join(out_dir, f'{video_name}.mp4')
    fps          = 30

    # collect and sort your images
    images = [img for img in os.listdir(image_folder)
            if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
    images.sort()

    if not images:
        raise RuntimeError(f"No images found in {image_folder}")

    # build full path to the first image and read it
    first_image_path = os.path.join(image_folder, images[0])
    frame = cv2.imread(first_image_path)
    if frame is None:
        raise RuntimeError(f"Failed to read {first_image_path}")

    height, width, layers = frame.shape

    # Use H.264 codec for web compatibility
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    video  = cv2.VideoWriter(video_out_path, fourcc, fps, (width, height))

    # write each frame
    for img_name in images:
        img_path = os.path.join(image_folder, img_name)
        img      = cv2.imread(img_path)
        if img is None:
            print(f"Warning: couldn't read {img_path}, skipping.")
            continue
        # optional: resize if your images vary in size
        if (img.shape[1], img.shape[0]) != (width, height):
            img = cv2.resize(img, (width, height))
        video.write(img)

    video.release()
    cv2.destroyAllWindows()
    print(f"Timelapse video '{video_name}' created successfully!")

# stitch_timelapse('/home/akami-3/gitlabsource/CloudCams/CloudCamImages/24caption',
#                   'cloudcam2025250724', 
#                   '/data/cloudcams/cloudcam2025/movies'
# )
