import cv2
import numpy as np
from astrometry import crop

# where we want the mean to settle
TARGET_MEAN = 52

# your camera’s limits
MIN_ETIME = 0.001
MAX_ETIME = 60.0
MIN_GAIN = 0
MAX_GAIN = 510
MIN_START_GAIN = 1

# Control gains
DEAD_BAND              = 1.5    # ± intensity within which we do nothing
K_ETIME_PER_LUX        = 0.1    # seconds per lux-unit of error
K_GAIN_PER_LUX         = 1.0    # gain-units per lux-unit of error

# Step caps
MAX_ETIME_STEP         = 1.0    # normal max sec/loop
MAX_GAIN_STEP          = 5      # normal max gain/loop

# Fast-path caps (for sunrise/sunset jumps)
FAST_THRESHOLD         = 30.0   # error above which we go into fast mode
MAX_ETIME_STEP_FAST    = 5.0    # larger exposure jump
MAX_GAIN_STEP_FAST     = 20     # larger gain jump

def check_brightness(image):
   mean_intensity = np.mean(image)
   print(f"mean pix intensity: {mean_intensity}")

   if mean_intensity > 160:
       return "Over-bright", mean_intensity
   elif mean_intensity < 40:
       return "Under-bright", mean_intensity
   else:
       return "Properly bright", mean_intensity
    

# # test img brightness
# img = cv2.imread('/opt/cloudcams/code/cropped.png')
# gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
# check_brightness(img)


def calculate_new_brightness_settings(mean_intensity, curr_etime, curr_gain):
    """
    - If |error| > FAST_THRESHOLD, allow bigger steps (sunrise/sunset fast mode).
    - Otherwise, use small, smooth adjustments.
    - Always keep gain as low as possible.
    """
    diff = mean_intensity - TARGET_MEAN  # + → too bright, - → too dark
    if abs(diff) <= DEAD_BAND:
        return curr_etime, curr_gain

    # pick appropriate caps
    if abs(diff) > FAST_THRESHOLD:
        max_etime = MAX_ETIME_STEP_FAST
        max_gain  = MAX_GAIN_STEP_FAST
    else:
        max_etime = MAX_ETIME_STEP
        max_gain  = MAX_GAIN_STEP

    # compute proportional steps
    etime_step = min(abs(diff) * K_ETIME_PER_LUX, max_etime)
    gain_step  = min(abs(diff) * K_GAIN_PER_LUX,  max_gain)

    new_etime = curr_etime
    new_gain  = curr_gain

    if diff > 0:
        # too bright → darken: lower gain first
        if curr_gain > MIN_GAIN:
            new_gain = max(curr_gain - gain_step, MIN_GAIN)
        else:
            new_etime = max(curr_etime - etime_step, MIN_ETIME)
    else:
        # too dark → brighten: raise exposure first
        if curr_etime < MAX_ETIME:
            new_etime = min(curr_etime + etime_step, MAX_ETIME)
        else:
            new_gain = min(curr_gain + gain_step, MAX_GAIN)

    # clamp to hard limits
    new_etime = float(np.clip(new_etime, MIN_ETIME, MAX_ETIME))
    new_gain  = int(  np.clip(new_gain,  MIN_GAIN,   MAX_GAIN))

    return new_etime, new_gain

def adjust_brightness(image, curr_etime, curr_gain):
    # gray_img = cv2.imread(image, cv2.IMREAD_GRAYSCALE) # for testing
    np_img = crop(image)
    gray_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
    status, mean_val = check_brightness(gray_img)
    print(f"{status} (mean={mean_val:.1f})")
    etime, gain = calculate_new_brightness_settings(mean_val, curr_etime, curr_gain)
    print(f"Suggest etime={etime:.3f}s, gain={gain}")
    return etime, gain
    