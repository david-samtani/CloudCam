# # import subprocess
# # from datetime import datetime

# # def log_status(value):
# #     path = "/i/cloudcam/camera/status"
# #     comment = "Camera Operational Status"
# #     try:
# #         subprocess.run([
# #             "ssPut", 
# #             f"NAME={path}", 
# #             f"VALUE={value}", 
# #             f"COMMENT={comment}"], 
# #             check=True)
# #     except subprocess.CalledProcessError as e:
# #         print(f"Error logging status (exit {e.returncode}): {e}")
# #     except Exception as e:
# #         print(f"Error logging status: {e}")

# # log_status("OFF")


# import warnings
# from astropy.stats import sigma_clipped_stats
# from photutils.detection import DAOStarFinder
# from photutils.utils.exceptions import NoDetectionsWarning
# import cv2
# import numpy as np
# import astrometry

# # def visible_stars(input_img_path):
# #     # convert image to cropped,2d numpy array
# #     img = astrometry.crop(input_img_path)

# #     data = np.mean(img, axis=2)

# #     mean, median, std = sigma_clipped_stats(data, sigma=3.0)
    
# #     daofind = DAOStarFinder(fwhm=3.0, threshold=5.0*std)
# #     if daofind is None:
# #         print(f"Error reading image: {input_img_path}")
# #         return False

# #     try:
# #         with warnings.catch_warnings():
# #             warnings.simplefilter('ignore', NoDetectionsWarning)
# #             sources = daofind(data - median)

# #         if sources is None or len(sources) == 0:
# #             print(f"No stars detected in {input_img_path}")
# #             return False
# #         else:
# #             print(f"Detected {len(sources)} stars in {input_img_path}")
# #             return True

# #     except Exception as e:
# #         print(f"Star-detection error: {input_img_path}: {e}")
# #         return False

# def visible_stars(input_img_path,
#                   threshold_sigma: float = 3.0,
#                   fwhm: float = 2.5,
#                   sat_level: float = 250,
#                   std_eps: float = 1e-3):
#     """
#     Return True if at least one star is found in the cropped image.
#     Bail early if the background has zero (or near-zero) variation.
#     """
#     # 1) load & crop
#     img = astrometry.crop(input_img_path)
#     if img is None or not isinstance(img, np.ndarray):
#         print(f"ERROR: can’t open/crop {input_img_path}")
#         return False

#     # 2) grayscale → 2D
#     if img.ndim == 3 and img.shape[2] == 3:
#         data = np.mean(img, axis=2)
#     else:
#         data = img.astype(float)

#     # 3) mask out saturated pixels
#     mask = data >= sat_level

#     # 4) compute background stats
#     mean, median, std = sigma_clipped_stats(data, sigma=3.0, mask=mask)
#     print(f"[DEBUG] mean={mean:.2f}, median={median:.2f}, std={std:.4f}")

#     #  → if there’s essentially no variation, there can’t be real stars
#     if std < std_eps:
#         print(f"[DEBUG] std ({std:.4f}) < eps ({std_eps}), no stars possible")
#         return False

#     # 5) set up DAOStarFinder
#     threshold = threshold_sigma * std
#     print(f"[DEBUG] using threshold = {threshold_sigma}σ → {threshold:.2f}")
#     daofind = DAOStarFinder(fwhm=fwhm, threshold=threshold)

#     # 6) run detection
#     try:
#         with warnings.catch_warnings():
#             warnings.simplefilter('ignore', NoDetectionsWarning)
#             sources = daofind(data - median)
#     except Exception as e:
#         print(f"Star‑detection error: {e}")
#         return False

#     # 7) interpret results
#     if sources is None or len(sources) == 0:
#         print(f"No stars detected in {input_img_path}")
#         return False

#     print(f"Detected {len(sources)} stars in {input_img_path}")
#     return True



# print(visible_stars('/home/akami-3/gitlabsource/CloudCams/src/cloudcam2250715-091412.jpg'))

# import automated_process

# automated_process.add_caption('/home/akami-3/gitlabsource/CloudCams/src/OVRcloudcam2250715-091412.jpg', '/home/akami-3/gitlabsource/CloudCams/src/')
import cv2
import os
import re
from datetime import datetime
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import astrometry
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

# add_caption('/home/akami-3/gitlabsource/CloudCams/CloudCamOVR/CloudCamOVR250723/OVRcloudcam2250723-091754.jpg', '/home/akami-3/gitlabsource/CloudCams/src/')

for image in os.listdir('/home/akami-3/gitlabsource/CloudCams/CloudCamImages/summitcaption'):
    astrometry.overlay(f'/home/akami-3/gitlabsource/CloudCams/CloudCamImages/summitcaption/{image}',
                        '/home/akami-3/gitlabsource/CloudCams/summitwesternover',
                        constellations='_westernconst',
                        stars='_westernstars',
                        planets='_planets')
