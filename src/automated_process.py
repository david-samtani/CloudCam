import numpy as np
import subprocess
import os
from take_image import capture_image
import cv2
from datetime import datetime, timedelta
import astrometry
import time
import subprocess
from timeslapse import stitch_timeslapse, show_recent_timeslapse
import shutter_control
from multiprocessing import Process, Manager
import warnings
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
from photutils.utils.exceptions import NoDetectionsWarning
import re

def add_caption(image_path, out_dir):
    image = cv2.imread(image_path)
    if image is None:
        raise RuntimeError(f"Failed to read image at {image_path!r}")

    # get date for timestamp from filename
    img_name = os.path.basename(image_path)
    # Extract the datetime string from the filename using regex
    match = re.search(r'(\d{3})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})', img_name)

    if not match:
        raise ValueError(f"Could not extract datetime from filename: {img_name}")

    groups = match.groups()
    year = str(int(groups[0]) + 1800)  # Convert 225 to 2025
    today = datetime.strptime(f"{year}-{groups[1]}-{groups[2]}", "%Y-%m-%d")
    day_of_week = today.strftime('%a')
    caption_datetime = f"{year}-{groups[1]}-{groups[2]} {day_of_week} {groups[3]}:{groups[4]}:{groups[5]}"

    adjusted_img = cv2.putText(image,
                    f'Cloud Cam {caption_datetime}', 
                    (25, 1377), 
                    cv2.FONT_HERSHEY_DUPLEX, 
                    1.75, 
                    (255,255,255), 
                    4
                    )

    output_name = os.path.basename(image_path)
    output_path = os.path.join(out_dir, output_name)
    cv2.imwrite(output_path, adjusted_img)

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

# def visible_stars(input_img_path):
#     # convert image to cropped,2d numpy array
#     img = astrometry.crop(input_img_path)
#     if img is None:
#         print(f"Failed to load image: {input_img_path}")
#         return False
        
#     try:
#         data = np.mean(img, axis=2)
#         mean, median, std = sigma_clipped_stats(data, sigma=3.0)
#         daofind = DAOStarFinder(fwhm=3.0, threshold=5.0*std)
        
#         with warnings.catch_warnings():
#             warnings.simplefilter('error', NoDetectionsWarning)
#             try:
#                 sources = daofind(data - median)
#             except NoDetectionsWarning:
#                 return False

#         # stars were detected
#         return True
        
#     except Exception as e:
#         print(f"Error processing image for star detection: {e}")
#         return False

def wait_until(target_time):
    now = datetime.now()
    delta = (target_time - now).total_seconds()
    if delta > 0:
        time.sleep(delta)


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

def image_capture(window_name, sunrise, img_out_dir, img_ovr_out_dir):
    # wcs file exists flag
    wcs_file_exists = False
    if os.path.exists('/home/akami-3/gitlabsource/CloudCams/astrometrynet_files/initial.wcs'):
        wcs_file_exists = True

    # have reset wcs file flag
    reset_wcs = True

    # log status
    log_status("ON")

    # show popup window after 30 min
    thirty_min_end = time.time() + 1800
    while datetime.now() > sunrise:
        if wcs_file_exists == False:
            print("WCS file does not exist, generating now ...")

            # capture image but if there is a network issue, retry
            image_path = capture_with_timeout(img_out_dir, timeout=90)
            print(image_path)

            try:
                astrometry.recalibrate_wcs(image_path)
                time.sleep(10)  # give some time for the WCS file to be created
            except Exception as e:
                print(f"Error running solve-field: {e}")
                time.sleep(10)
                continue
            
            print("wcs recalibrated successfully.")
            reset_wcs = True

        # show images for 10 seconds
        t_end = time.time() + 10
        while time.time() < t_end:
            # capture image but if there is a network issue, retry
            image_path = capture_with_timeout(img_out_dir, timeout=90)
            print(image_path)

            # recalibrate wcs file
            if reset_wcs == False:
                try:
                    astrometry.recalibrate_wcs(image_path)
                    print("wcs recalibrated successfully.")
                    reset_wcs = True
                except Exception as e:
                    print(f"Error running solve-field: {e}")
                    time.sleep(10)
        
            new_image_path = astrometry.overlay(image_path, img_ovr_out_dir, False, True)
            print(new_image_path)
            add_caption(new_image_path, img_out_dir)

            # show newly captured image
            update_image(window_name, new_image_path)

        while time.time() > thirty_min_end:
            # show timelapse of recently captured images (past 30 min)
            show_recent_timeslapse(img_ovr_out_dir, window_name)
            # show popup window after 30 min
            thirty_min_end = time.time() + 20

    # log status
    log_status("OFF")

def update_image(window_name, img_path):
    try:
        img = cv2.imread(img_path)
        if img is None:
            print(f"Could not open image {img_path}")
            return
        
        cv2.imshow(window_name, img)
        cv2.waitKey(1)  # Use shorter wait time, non-blocking
    except Exception as e:
        print(f"Error displaying image: {e}")
        # If display fails, we'll continue without showing the image

def main():
    workpath = '/cloudcams/'

    # create necessary directories if they don't exist
    now = datetime.now()
    if f'{workpath}cloudcamimages' not in os.listdir(workpath):
        os.makedirs(f'{workpath}cloudcamimages', exist_ok=True)
    if f'{workpath}cloudcamovr' not in os.listdir(workpath):
        os.makedirs(f'{workpath}cloudcamovr', exist_ok=True)
    if f'{workpath}timeslapses' not in os.listdir(workpath):
        os.makedirs(f'{workpath}timeslapses', exist_ok=True)

    # make taken images dir for that day
    out_dir_name = f'cloudcam{now.strftime("%y%m%d")}'
    if f'{workpath}cloudcamimages/{out_dir_name}' not in os.listdir(f'{workpath}cloudcamimages'):
        os.makedirs(f'{workpath}cloudcamimages/{out_dir_name}', exist_ok=True)

    # make overlay images dir for that day
    out_ovr_dir_name = f'cloudcamovr{now.strftime("%y%m%d")}'
    if f'{workpath}cloudcamovr/{out_ovr_dir_name}' not in os.listdir(f'{workpath}cloudcamovr'):
        os.makedirs(f'{workpath}cloudcamovr/{out_ovr_dir_name}', exist_ok=True)

    # set output directories
    img_out_dir = f'{workpath}cloudcamimages/{out_dir_name}/'
    img_ovr_out_dir = f'{workpath}cloudcamovr/{out_ovr_dir_name}/'
    timeslapses_dir = f'{workpath}timeslapses/'

    # get end of night timelapse's name
    timeslapse_name = f'cloudcamtimeslapse25{now.strftime("%y%m%d")}'

    # set up the window
    window_name = 'CloudCam'

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

            # popup window to show recent images
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            image_capture(window_name, sunrise, img_out_dir, img_ovr_out_dir)
            cv2.destroyWindow(window_name)
        elif now.hour < 12 and now > sunrise:
            # later morning (before noon), waiting for sunrise/set to reset, stop taking images
            noon_today = now.replace(hour=12, minute=0, second=0, microsecond=0)
            print(f"{datetime.now()}: Waiting until sunrise/set times are reset")

            # # close shutter until noon
            # shutter_control.set_gpio('close')

            wait_until(noon_today)
            continue
        
        # afternoon, wait for sunset
        if now.hour >= 12 and now < sunset:
            print(f"{datetime.now()}: Waiting until sunset")

            # # close shutter until sunset
            # shutter_control.set_gpio('close')

            wait_until(sunset)

        # night, start taking images until sunrise
        print(f"{datetime.now()}: Turned night/is night")

        # # open shutter images until sunrise
        # shutter_control.set_gpio('OPEN')

        # popup window to show recent images
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        image_capture(window_name, sunrise, img_out_dir, img_ovr_out_dir)
        cv2.destroyWindow(window_name)

        # morning begins, stop taking images
        print(f"{datetime.now()}: Turned day")

        # # close shutter unitl next night
        # shutter_control.set_gpio('close')

        # create timeslapse
        stitch_timeslapse(img_ovr_out_dir, timeslapse_name, timeslapses_dir)


if __name__ == "__main__":
    main()
