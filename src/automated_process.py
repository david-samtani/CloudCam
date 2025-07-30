import numpy as np
import subprocess
import os
import shutil
from take_image import capture_image
import cv2
from datetime import datetime, timedelta
import astrometry
import time
import subprocess
import timelapse
import shutter_control
from multiprocessing import Process, Manager
import warnings
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
from photutils.utils.exceptions import NoDetectionsWarning
import re
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def add_caption(image_path, out_dir):
    # Read main image
    image = cv2.imread(image_path)
    if image is None:
        raise RuntimeError(f"Failed to read image at {image_path!r}")

    # Read logo with alpha channel
    logo = cv2.imread('/home/akami-3/gitlabsource/CloudCams/graphics/cfh_logo.png', cv2.IMREAD_UNCHANGED)
    if logo is None:
        raise RuntimeError("Failed to read logo image")

    # Scale logo to desired size 
    scale_factor = 0.75
    logo_height = int(logo.shape[0] * scale_factor)
    logo_width = int(logo.shape[1] * scale_factor)
    logo = cv2.resize(logo, (logo_width, logo_height))

    # Calculate position for logo (bottom right with padding)
    padding = 25
    y_offset = image.shape[0] - logo_height - padding
    x_offset = image.shape[1] - logo_width - padding

    # Get the alpha channel and normalize it to range 0-1
    alpha_channel = logo[:, :, 3] / 255.0
    # Create 3D alpha matrix
    alpha_3d = np.dstack([alpha_channel] * 3)

    # Extract BGR channels from logo
    logo_bgr = logo[:, :, :3]

    # Get the region of interest from the main image
    roi = image[y_offset:y_offset + logo_height, x_offset:x_offset + logo_width]

    # Blend the logo with the ROI using the alpha channel
    blended = (logo_bgr * alpha_3d + roi * (1 - alpha_3d)).astype(np.uint8)

    # Place the blended result back into the main image
    image[y_offset:y_offset + logo_height, x_offset:x_offset + logo_width] = blended

    # Get date for timestamp from filename
    img_name = os.path.basename(image_path)
    match = re.search(r'(\d{3})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})', img_name)

    if not match:
        raise ValueError(f"Could not extract datetime from filename: {img_name}")

    groups = match.groups()
    year = str(int(groups[0]) + 1800)  # Convert 225 to 2025
    today = datetime.strptime(f"{year}-{groups[1]}-{groups[2]}", "%Y-%m-%d")
    day_of_week = today.strftime('%a')
    caption_datetime = f"{year}-{groups[1]}-{groups[2]} {day_of_week} {groups[3]}:{groups[4]}:{groups[5]}"
    # Get text size to create appropriate background
    text = f'{caption_datetime} HST'
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.75
    thickness = 4
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    
    # Draw black background rectangle
    padding = 10  # Padding around text
    cv2.rectangle(image, 
                 (20, 1332),  # Moved up by 20 pixels
                 (25 + text_width + padding, 1377 + padding),
                 (0, 0, 0),  # Black color
                 -1)  # Filled rectangle
    
    # Draw text
    image = cv2.putText(image,
                text,
                (25, 1377),
                font,
                font_scale,
                (255, 255, 255),  # White color
                thickness)

    output_name = os.path.basename(image_path)
    output_path = os.path.join(out_dir, output_name)
    cv2.imwrite(output_path, image)
    print(f"Caption and logo added to {output_name} and saved to {out_dir}")

def fetch_time(key):
    try:
        cmd = ["ssGet", f"/t/ephem/{key}"]
        raw = subprocess.check_output(cmd)
        raw_str = raw.decode().strip()
        return datetime.strptime(raw_str, "%d-%b-%Y %H:%M:%S")
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}. Error: {e}")
        return None
    except Exception as e:
        print(f"Error fetching time for {key}: {e}")
        return None

def log_status(value):
    while True:
        path = "/i/cloudcam/camera/status"
        comment = "Camera Operational Status"
        try:
            subprocess.run([
                "ssPut", 
                f"NAME={path}", 
                f"VALUE={value}", 
                f"COMMENT={comment}"], 
                check=True)
            break
        except subprocess.CalledProcessError as e:
            print(f"Error logging status (exit {e.returncode}): {e}, retrying...")
        except Exception as e:
            print(f"Error logging status: {e}, retrying...")

def wait_until(target_time):
    now = datetime.now()
    delta = (target_time - now).total_seconds()
    if delta > 0:
        time.sleep(delta)

def show_recent_timelapse(in_dir, window_name, pause_time=0.2, output_name="temp_timelapse.mp4"):
    global current_fig

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

    # Create temp directory if it doesn't exist
    temp_dir = "/home/akami-3/gitlabsource/CloudCams/temp_timelapse"
    os.makedirs(temp_dir, exist_ok=True)

    # temporary video file
    out_path = os.path.join(temp_dir, output_name)

    # use OpenCV to create timelapse
    frame = cv2.imread(image_paths[0])
    if frame is None:
        print(f"Failed to read first frame from {image_paths[0]}")
        return

    height, width = frame.shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(out_path, fourcc, 10, (width, height))

    try:
        for img_path in image_paths:
            img = cv2.imread(img_path)
            if img is not None:
                writer.write(img)
    finally:
        writer.release()

    # play the video
    cap = cv2.VideoCapture(out_path)

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            # show the frame on existing matplotlib window
            plt.clf()
            ax = current_fig.add_subplot(111)
            current_fig.canvas.manager.set_window_title(window_name)
            ax.imshow(frame)
            ax.axis('off')

            # Update display
            current_fig.canvas.draw()
            current_fig.canvas.flush_events()
            plt.pause(pause_time)  # Keep GUI responsive
    finally:
        cap.release()
        

def capture_worker(img_out_dir, result_list):
    try:
        result_list.append(capture_image(img_out_dir))
    except Exception as e:
        result_list.append(e)

def capture_with_timeout(img_out_dir, timeout=90):
    mgr   = Manager()
    result = mgr.list()

    while True:
        p = Process(target=capture_worker, args=(img_out_dir, result))
        p.start()
        p.join(timeout)

        if p.is_alive():
            p.terminate()
            p.join()
            print(f"capture_image took too long (>{timeout}s), retrying...")
            log_status("Image Capture Timeout, retrying...")
            continue

        val = result[0] if result else None
        if isinstance(val, Exception):
            print(f"capture_image raised an exception: {val!r}, retrying...")
            log_status("Image Capture Exception, retrying...")
            result[:] = []  # clear
            time.sleep(10)
            continue

        return val  # success path

def show_image(window_name, img_path, pause_time=0.2):
    global current_fig

    try:
        # Create window only if it doesn't exist
        if 'current_fig' not in globals() or current_fig is None:
            plt.ion()  # Interactive mode on
            current_fig = plt.figure()
            ax = current_fig.add_subplot(111)
            current_fig.canvas.manager.set_window_title(window_name)
        else:
            # Clear the current axes but keep the window
            plt.clf()
            ax = current_fig.add_subplot(111)
            current_fig.canvas.manager.set_window_title(window_name)

        # Load and display new image
        img = mpimg.imread(img_path)
        if img is None:
            print(f"Could not open image {img_path}")
            return

        ax.imshow(img)
        ax.axis('off')
        
        # Update display
        current_fig.canvas.draw()
        current_fig.canvas.flush_events()
        plt.pause(pause_time)  # Keep GUI responsive

    except Exception as e:
        print(f"Error displaying image: {e}")
        if 'current_fig' in globals() and current_fig is not None:
            plt.close(current_fig)
            current_fig = None
        # If display fails, the process will continue without showing the image and no retry will be attempted.

def nas_save_raw_image(image_path, nas_img_dir, nas_raw_dir_path, nas_movie_dir_path):
    # save to the nas raw image sub directory
    image_name = os.path.basename(image_path)
    nas_raw_img_path = os.path.join(nas_raw_dir_path, image_name)
    shutil.copy(image_path, nas_raw_img_path)

    # save latest raw image to the nas
    nas_img_name = f"cloudcam2025_raw.jpg"
    nas_img_path = os.path.join(nas_img_dir, nas_img_name)
    shutil.copy(image_path, nas_img_path)
    print(f"Overlay created and saved to the NAS from: {image_path} to {nas_img_path}")

    # save latest movie image (raw image with caption)
    add_caption(image_path, nas_movie_dir_path)

    # save thumbnail image to the nas
    thumbnail_image_name = "cloudcam2025small.jpg"
    nas_thumbnail_image_path = os.path.join(nas_img_dir, thumbnail_image_name)
    shutil.copy(image_path, nas_thumbnail_image_path)

def update_latest_images(updated_image_path, nas_img_dir):
    # save all types of sleeping images to the nas
    for constellations in ['_westernconst', '_hawaiianconst', '']:
        for stars in ['_westernstars', '_hawaiianstars', '']:
            for planets in ['_planets', '']:
                try:
                    if constellations == '' and stars == '' and planets == '':
                        nas_img_name = "cloudcam2025_raw.jpg"
                        nas_img_path = os.path.join(nas_img_dir, nas_img_name)
                        shutil.copy(updated_image_path, nas_img_path)
                        continue
                    # save latest variation of overlayed image to the nas
                    nas_img_name = f"cloudcam2025{constellations}{stars}{planets}.jpg"
                    nas_img_path = os.path.join(nas_img_dir, nas_img_name)
                    shutil.copy(updated_image_path, nas_img_path)
                    print(f"Status image saved to the NAS from: {updated_image_path} to {nas_img_path}")
                except Exception as e:
                    print(f"Error saving sleeping image for {constellations} with stars {stars} and planets {planets}: {e}")

def image_capture(window_name, sunrise, img_out_dir, img_ovr_out_dir, nas_img_dir, nas_raw_dir_path, nas_movie_dir_path):
    # Initialize flags
    wcs_file_exists = os.path.exists('/home/akami-3/gitlabsource/CloudCams/astrometrynet_files/initial.wcs')
    reset_wcs = False ############# change back later
    thirty_min_past = False

    # capture image to recalibrate wcs but if there is a network issue, retry
    image_path = capture_with_timeout(img_out_dir, timeout=90)
    print(image_path)
    # show image
    show_image(window_name, image_path, pause_time=0.2)
    # save raw image to the nas
    nas_save_raw_image(image_path, nas_img_dir, nas_raw_dir_path, nas_movie_dir_path)

    # update latest overlay images status message
    overlay_not_available_image_path = '/home/akami-3/gitlabsource/CloudCams/website/overlay-not-available.jpg'
    for constellations in ['_westernconst', '_hawaiianconst', '']:
        for stars in ['_westernstars', '_hawaiianstars', '']:
            for planets in ['_planets', '']:
                try:
                    if constellations == '' and stars == '' and planets == '':
                        continue
                    # save latest variation of overlayed image to the nas
                    nas_img_name = f"cloudcam2025{constellations}{stars}{planets}.jpg"
                    nas_img_path = os.path.join(nas_img_dir, nas_img_name)
                    shutil.copy(overlay_not_available_image_path, nas_img_path)
                    print(f"Sleeping image saved to the NAS from: {overlay_not_available_image_path} to {nas_img_path}")
                except Exception as e:
                    print(f"Error saving sleeping image for {constellations} with stars {stars} and planets {planets}: {e}")

    # log status
    log_status("ON")

    # Initialize timing
    thirty_min_end = time.time() + 1800
    two_min_end = None

    while datetime.now() < sunrise: ################## change back later
        # Handle WCS calibration
        if not wcs_file_exists:
            try:
                astrometry.recalibrate_wcs(image_path)
                time.sleep(10)  # Wait for WCS file creation

                # Only set flags if file actually exists after successful recalibration
                if os.path.exists('/home/akami-3/gitlabsource/CloudCams/astrometrynet_files/initial.wcs'):
                    wcs_file_exists = True
                    reset_wcs = True
                    print("WCS recalibrated successfully.")
                else:
                    print("WCS recalibration failed - file not created")
                    wcs_file_exists = False
                    reset_wcs = False
            except Exception as e:
                wcs_file_exists = False
                reset_wcs = False
                print(f"Error running solve-field: {e} - retrying...")

        image_path = capture_with_timeout(img_out_dir, timeout=90)
        print(f"New capture: {image_path}")
        # show image
        show_image(window_name, image_path, pause_time=0.2)
        # save raw image to the nas
        nas_save_raw_image(image_path, nas_img_dir, nas_raw_dir_path, nas_movie_dir_path)

        # Process and display image
        if wcs_file_exists:
            if not reset_wcs:
                try:
                    astrometry.recalibrate_wcs(image_path)
                    time.sleep(10)  # Wait for WCS file creation

                    # Only set flags if file actually exists after successful recalibration
                    if os.path.exists('/home/akami-3/gitlabsource/CloudCams/astrometrynet_files/initial.wcs'):
                        wcs_file_exists = True
                        reset_wcs = True
                        print("WCS recalibrated successfully.")
                    else:
                        print("WCS recalibration failed - file not created")
                        wcs_file_exists = False
                        reset_wcs = False
                except Exception as e:
                    wcs_file_exists = False
                    reset_wcs = False
                    print(f"Error running solve-field: {e} - continuing...")
        
        if wcs_file_exists:
            # create all types of overlays for the server (for website)
            for constellations in ['_westernconst', '_hawaiianconst', '']:
                for stars in ['_westernstars', '_hawaiianstars', '']:
                    # planets can be _planets for True or '' for False
                    for planets in ['_planets', '']:
                        try:
                            # raw images are saved to the nas after they are taken
                            if constellations == '' and stars == '' and planets == '':
                                print("No constellations, stars, or planets requested. Skipping overlay.")
                                continue
                            new_image_path = astrometry.overlay(image_path, img_ovr_out_dir, constellations=constellations, stars=stars, planets=planets)
                            # save latest variation of overlayed image to the nas
                            nas_img_name = f"cloudcam2025{constellations}{stars}{planets}.jpg"
                            nas_img_path = os.path.join(nas_img_dir, nas_img_name)
                            shutil.copy(new_image_path, nas_img_path)
                            print(f"Overlay created and saved to the NAS from: {new_image_path} to {nas_img_path}")
                        except Exception as e:
                            print(f"Error creating overlay for {constellations} with stars {stars} and planets {planets}: {e}")

            # overlay that will save locally (optional)
            new_image_path = astrometry.overlay(image_path, img_ovr_out_dir, constellations='_hawaiianconst', stars='_hawaiianstars', planets='_planets')
            add_caption(new_image_path, img_ovr_out_dir)
            show_image(window_name, new_image_path, pause_time=0.2)

    # if 30 min has passed, show past thirty min of images in a timelapse
    if time.time() > thirty_min_end and thirty_min_past == False:
        thirty_min_past = True
        two_min_end = time.time() + 120

    # if 30 min has passed, show past thirty min of images in a timelapse
    if thirty_min_past == True and time.time() > two_min_end:
        # show timelapse of recently captured images (past 30 min)
        show_recent_timelapse(img_ovr_out_dir, window_name)
        # reset two_min_end for next cycle
        two_min_end = time.time() + 120

    ## clean up
    # save all types of sleeping images to the nas
    sleeping_image_path = '/home/akami-3/gitlabsource/CloudCams/website/cloudcam2025small.jpg'
    update_latest_images(sleeping_image_path, nas_img_dir)
    # save sleeping thumbnail to nas
    nas_sleeping_thumbnail_path = os.path.join(nas_img_dir, "cloudcam2025small.jpg")
    shutil.copy(sleeping_image_path, nas_sleeping_thumbnail_path)
    # delete temporary cropped image used for recalibrating WCS
    cropped_image_path = os.path.join(img_out_dir, 'cropped.jpg')
    if os.path.exists(cropped_image_path):
        os.remove(cropped_image_path)
    # close window
    plt.close()
    # log status
    log_status("OFF")

def main():
    now = datetime.now()

    date = now.strftime("%y%m%d")
    # make today's images dir for the nas
    nas_img_dir = f'/data/cloudcams/cloudcam2025'
    td_nas_dir_name = f'{date}'
    nas_raw_dir_path = f'{nas_img_dir}/{td_nas_dir_name}'
    os.makedirs(nas_raw_dir_path, exist_ok=True)
    # make a directory for the movie images for today (to make timelapse)
    nas_movie_dir_name = f'{date}_movie'
    nas_movie_dir_path = os.path.join(nas_img_dir, nas_movie_dir_name)
    os.makedirs(nas_movie_dir_path, exist_ok=True)
    # make movies (timelapses) dir for the nas
    nas_timelapse_dir = os.path.join(nas_img_dir, 'movies')
    os.makedirs(nas_timelapse_dir, exist_ok=True)
    # set today's nas timelapse name
    nas_timelapse_name = f'cloudcam2025{date}'

    # make taken images dir for that day
    out_dir_name = f'CloudCam{date}'
    os.makedirs(f'/home/akami-3/gitlabsource/CloudCams/CloudCamImages/{out_dir_name}', exist_ok=True)
    # make overlay images dir for that day
    out_ovr_dir_name = f'CloudCamOVR{date}'
    os.makedirs(f'/home/akami-3/gitlabsource/CloudCams/CloudCamOVR/{out_ovr_dir_name}', exist_ok=True)
    # set output directory
    img_out_dir = f'/home/akami-3/gitlabsource/CloudCams/CloudCamImages/{out_dir_name}'
    img_ovr_out_dir = f'/home/akami-3/gitlabsource/CloudCams/CloudCamOVR/{out_ovr_dir_name}'
    timelapses_dir = '/home/akami-3/gitlabsource/CloudCams/timelapses'
    # get end of night timelapse's name
    timelapse_name = f'cloudcamtimelapse{date}'
    # set up the window
    window_name = 'CloudCam Viewer'

    while True:
        # get current datetime
        now = datetime.now()
        # get initial sunset and sunrise times
        sunset  = fetch_time("sunsetTime")
        sunrise = fetch_time("sunriseTime")
        print(f"Current time: {now}, Sunrise: {sunrise}, Sunset: {sunset}")

        # if sunrise or sunset is None, wait for 1 minute and try again
        while sunrise is None or sunset is None:
            print("Waiting for sunrise or sunset times to be available...")
            time.sleep(60)
            now = datetime.now()
            sunset  = fetch_time("sunsetTime")
            sunrise = fetch_time("sunriseTime")
            print(f"Current time: {now}, Sunrise: {sunrise}, Sunset: {sunset}")

        # first if statment used for if camera is rebooted at night
        if now.hour < 12 and now < sunrise:
            # early morning (before sunrise), capture images until sunrise
            print(f"{datetime.now()}: Already night - starting image capture")

            # # open shutter until sunrise
            # shutter_control.set_gpio('OPEN')

            image_capture(window_name, sunrise, img_out_dir, img_ovr_out_dir, nas_img_dir, nas_raw_dir_path, nas_movie_dir_path)

        elif now.hour < 12 and now > sunrise:
            # later morning (before noon), waiting for sunrise/set to reset, stop taking images
            noon_today = now.replace(hour=12, minute=0, second=0, microsecond=0)
            print(f"{datetime.now()}: Waiting until sunrise/set times are reset")

            # # close shutter until noon
            # shutter_control.set_gpio('close')

            # update latest images status to sleeping
            update_latest_images('/home/akami-3/gitlabsource/CloudCams/website/blank-daylight.jpg', nas_img_dir)

            wait_until(noon_today)
            continue
        
        # afternoon, wait for sunset
        if now.hour >= 12 and now < sunset:
            print(f"{datetime.now()}: Waiting until sunset")

            # # close shutter until sunset
            # shutter_control.set_gpio('close')

            # update latest images status to sleeping
            update_latest_images('/home/akami-3/gitlabsource/CloudCams/website/blank-daylight.jpg', nas_img_dir)

            wait_until(sunset)

        # night, start taking images until sunrise
        print(f"{datetime.now()}: Turned night/is night")

        # # open shutter images until sunrise
        # shutter_control.set_gpio('OPEN')

        image_capture(window_name, sunrise, img_out_dir, img_ovr_out_dir, nas_img_dir, nas_raw_dir_path, nas_movie_dir_path)

        # morning begins, stop taking images
        print(f"{datetime.now()}: Turned day")

        # # close shutter unitl next night
        # shutter_control.set_gpio('close')

        # update latest images status to sleeping
        update_latest_images('/home/akami-3/gitlabsource/CloudCams/website/blank-daylight.jpg', nas_img_dir)

        # create timelapse of raw images to save to the nas
        timelapse.stitch_timelapse(nas_movie_dir_path, nas_timelapse_name, nas_timelapse_dir)

        # create timelapse to save locally (optional)
        timelapse.stitch_timelapse(img_ovr_out_dir, timelapse_name, timelapses_dir)
        
        continue

# # for testing
# def main():
#     now = datetime.now()
#     date = now.strftime("%y%m%d")
#     # make today's images dir for the nas
#     nas_img_dir = f'/data/cloudcams/cloudcam2025'
#     td_nas_dir_name = f'{date}'
#     nas_raw_dir_path = f'{nas_img_dir}/{td_nas_dir_name}'
#     os.makedirs(nas_raw_dir_path, exist_ok=True)

#     # make taken images dir for that day
#     out_dir_name = f'CloudCam{date}'
#     os.makedirs(f'/home/akami-3/gitlabsource/CloudCams/CloudCamImages/{out_dir_name}', exist_ok=True)

#     # make overlay images dir for that day
#     out_ovr_dir_name = f'CloudCamOVR{date}'
#     os.makedirs(f'/home/akami-3/gitlabsource/CloudCams/CloudCamOVR/{out_ovr_dir_name}', exist_ok=True)

#     # set output directory
#     img_out_dir = f'/home/akami-3/gitlabsource/CloudCams/CloudCamImages/{out_dir_name}'
#     img_ovr_out_dir = f'/home/akami-3/gitlabsource/CloudCams/CloudCamOVR/{out_ovr_dir_name}'
#     timelapses_dir = '/home/akami-3/gitlabsource/CloudCams/timelapses'

#     # get end of night timelapse's name
#     timelapse_name = f'cloudcamtimelapse25{date}'

#     # set up the window
#     window_name = 'CloudCam Viewer'

#     image_capture(window_name, fetch_time("sunriseTime"), img_out_dir, img_ovr_out_dir, nas_img_dir, nas_raw_dir_path, nas_movie_dir_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutdown requested via Ctrl+C...")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
    finally:
        print("Performing cleanup...")
        # Save sleeping images
        try:
            offline_image_path = '/home/akami-3/gitlabsource/CloudCams/website/cloudcam-offline.jpg'
            nas_img_dir = '/data/cloudcams/cloudcam2025'
            # save all types of sleeping images to the nas
            update_latest_images(offline_image_path, nas_img_dir)

            # save sleeping thumbnail to nas
            nas_sleeping_thumbnail_path = os.path.join(nas_img_dir, "cloudcam2025small.jpg")
            shutil.copy(offline_image_path, nas_sleeping_thumbnail_path)
        except Exception as e:
            print(f"Error saving offline image: {e}")
        
        # Close any open matplotlib windows
        plt.close('all')

        # Close shutter
        # shutter_control.set_gpio('close')

        # Log camera as OFF
        log_status("OFF")
        print("Cleanup complete")
