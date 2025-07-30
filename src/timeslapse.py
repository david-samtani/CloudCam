import cv2
import os
from datetime import datetime, timedelta

def stitch_timeslapse(in_dir, out_name, out_dir):
    image_folder = in_dir
    video_name   = out_name
    video_out_path = os.path.join(out_dir, f'{video_name}.mp4')
    fps          = 10

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

    # prepare your VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
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

# stitch_timeslapse('/opt/cloudcams/CloudCam225072-3overlayedimages',
#                   'video', 
#                   '/opt/cloudcams/timeslapses'
# )


def show_recent_timeslapse(in_dir, window_name, output_name="temp_timelapse.mp4"):
    workpath = '/opt/cloudcams/'

    # show past 30 min of taken images
    now = datetime.now()
    cutoff = now - timedelta(minutes=30)

    # collect and sort your images
    images = [img for img in os.listdir(in_dir)
            if img.lower().endswith(('.png', '.jpg', '.jpeg'))]

    # filter by modified time in the last 30 mins
    image_paths = [img for img in image_paths if datetime.fromtimestamp(os.path.getmtime(img)) > cutoff]
    image_paths.sort()

    if len(image_paths) < 2:
        print("Not enough images for a timelapse.")
        return

    # temporary video file
    out_path = os.path.join(f"{workpath}temp_timeslapse", output_name)

    # use OpenCV to create timelapse
    frame = cv2.imread(image_paths[0])
    height, width = frame.shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(out_path, fourcc, 10, (width, height))

    for img_path in image_paths:
        img = cv2.imread(img_path)
        if img is not None:
            writer.write(img)
    writer.release()

    # play the video
    cap = cv2.VideoCapture(out_path)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow(window_name, frame)
    cap.release()
    