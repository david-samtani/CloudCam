import cv2
import numpy as np
from astrometry import crop

# where we want the mean to settle
TARGET_MEAN = 46

# your camera’s limits
MIN_ETIME = 0.001
MAX_ETIME = 45.0
MIN_GAIN = 0
MAX_GAIN = 510

# Add these constants at the top of the file
MAX_ETIME_CHANGE = 2.5  # Maximum allowed change in exposure time per adjustment
MAX_GAIN_CHANGE = 50     # Maximum allowed change in gain per adjustment
MIN_ETIME_CHANGE = 0.001  # Minimum exposure time
MIN_GAIN_CHANGE = 1       # Minimum gain

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
# img = cv2.imread('/home/akami-3/gitlabsource/CloudCams/code/cropped.png')
# gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
# check_brightness(img)
def calculate_new_brightness_settings(mean_intensity, curr_etime, curr_gain):
    error = TARGET_MEAN - mean_intensity  # positive if image is too dark
        
    # Start with current settings
    new_etime = curr_etime
    new_gain = curr_gain
    
    # Tuning parameters - reduced sensitivity to prevent oscillation
    ETIME_BRIGHTNESS_SENSITIVITY = 1.07
    GAIN_BRIGHTNESS_SENSITIVITY = 0.3

    # Handle zero cases first
    if mean_intensity == 0:
        # If image is completely black, increase both exposure and gain
        new_etime = min(curr_etime + MAX_ETIME_CHANGE, MAX_ETIME)
        new_gain = min(curr_gain + MAX_GAIN_CHANGE, MAX_GAIN)
        return new_etime, new_gain
        
    # Calculate proportional changes, scaled by sensitivity
    if error > 0:  # Image too dark
        if curr_etime < MAX_ETIME:
            # Start with minimum exposure if current is zero
            if curr_etime == 0:
                new_etime = .5
            else:
                change_ratio = (TARGET_MEAN / mean_intensity)
                calc_etime = curr_etime * change_ratio
                delta_etime = abs(calc_etime - curr_etime) * ETIME_BRIGHTNESS_SENSITIVITY
                delta_etime = np.clip(delta_etime, MIN_ETIME_CHANGE, MAX_ETIME_CHANGE)
                new_etime = min(curr_etime + delta_etime, MAX_ETIME)
        elif curr_gain < MAX_GAIN:
            # Start with minimum gain if current is zero
            if curr_gain == 0:
                new_gain = 10
            else:
                change_ratio = (TARGET_MEAN / mean_intensity)
                calc_gain = curr_gain * change_ratio
                delta_gain = abs(calc_gain - curr_gain) * GAIN_BRIGHTNESS_SENSITIVITY
                print("delta_gain:", delta_gain, new_gain)
                delta_gain = np.clip(delta_gain, MIN_GAIN_CHANGE, MAX_GAIN_CHANGE)
                new_gain = min(curr_gain + delta_gain, MAX_GAIN)
    else:  # Image too bright
        if curr_gain > MIN_GAIN:
            change_ratio = TARGET_MEAN / mean_intensity
            calc_gain = curr_gain * change_ratio
            delta_gain = abs(calc_gain - curr_gain) * GAIN_BRIGHTNESS_SENSITIVITY
            print("delta_gain:", delta_gain, new_gain)
            delta_gain = np.clip(delta_gain, MIN_GAIN_CHANGE, MAX_GAIN_CHANGE)
            new_gain = max(curr_gain - delta_gain, MIN_GAIN)
        elif curr_etime > MIN_ETIME:
            change_ratio = TARGET_MEAN / mean_intensity
            calc_etime = curr_etime * change_ratio
            delta_etime = abs(calc_etime - curr_etime) * ETIME_BRIGHTNESS_SENSITIVITY
            delta_etime = np.clip(delta_etime, MIN_ETIME_CHANGE, MAX_ETIME_CHANGE)
            new_etime = max(curr_etime - delta_etime, MIN_ETIME)

    # Final clamp to bounds
    new_etime = float(np.clip(new_etime, MIN_ETIME, MAX_ETIME))
    new_gain = int(np.clip(new_gain, MIN_GAIN, MAX_GAIN))

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
    