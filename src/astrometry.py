import cv2
import numpy as np
import os
from astropy.io import fits
from astropy.time import Time
from astropy import units as u
import subprocess
from astropy.wcs import WCS
from astropy.coordinates import EarthLocation, SkyCoord, AltAz
from skyfield.api import load, wgs84, EarthSatellite
import re
from datetime import timezone
# for test to get cropped image
from PIL import Image

def save_initial_wcs_values():
    global initial_utc, initial_ra, initial_dec
    with open('/home/akami-3/gitlabsource/CloudCams/astrometrynet_files/initial_wcs_values.txt', 'w') as f:
        # Write values in a parseable format: ISO time, ra in deg, dec in deg
        f.write(f"{initial_utc.isot} {initial_ra.value} {initial_dec.value}")

def load_initial_wcs_values():
    global initial_utc, initial_ra, initial_dec
    try:
        with open('/home/akami-3/gitlabsource/CloudCams/astrometrynet_files/initial_wcs_values.txt', 'r') as f:
            data = f.read().split()
            # data[0] is ISO time, data[1] is ra in deg, data[2] is dec in deg
            initial_utc = Time(data[0], format='isot', scale='utc')
            initial_ra = float(data[1]) * u.deg
            initial_dec = float(data[2]) * u.deg
    except FileNotFoundError:
        print("Initial values file not found. Must recalibrate_wcs first.")

# Initialize global variables
initial_utc = None
initial_ra = None
initial_dec = None

def crop(img_source):
    # if img_source is a filename, read it, but if its an array alr, use it
    if isinstance(img_source, str):
        img = cv2.imread(img_source)
    else:
        img = img_source.copy()

    # create polygon to keep
    sky_poly = np.array([
        # [0, 0],  # top-left
        # [img.shape[1], 0],  # top-right
        # [img.shape[1], 1302],
        # [1504, 1302],
        # [1501, 1280],
        # [1428, 1283],
        # [1428, 1302],
        # [1167, 1302],
        # [1084, 1300],
        # [1001, 1270],
        # [933, 1300],
        # [602, 1313],
        # [201, 1273],
        # [37, 1254],
        # [0, 1214]

        # [0, 0],  # top-left
        # [img.shape[1], 0],  # top-right
        # [img.shape[1], float(img.shape[0]) * .875],  # bottom-right
        # [0, float(img.shape[0]) * .875],  # bottom-left

        [322, 0],
        [621, 0],
        [672, 43],
        [670, 73],
        [766, 151],
        [788, 145],
        [2053, 1189],
        [1794, 1162],
        [1625, 1186],
        [842, 1281],
        [1399, 1286],
        [1218, 1195],
        [949, 1351],
        [535, 1354],
        [433, 1152],
        [209, 1219],
        [153, 1109],
        [5, 1049]
    ], dtype=np.int32)

    # Create mask
    mask = np.zeros(img.shape[:2], dtype=np.uint8)

    # fill polygon
    cv2.fillPoly(mask, [sky_poly], 255)

    # black out outside of polygon
    inv = cv2.bitwise_not(mask)
    img[inv==255] = (0,0,0)

    return img

# # test to show cropped image
# img = crop('/home/akami-3/gitlabsource/CloudCams/code/adjusted2025-07-08 09:29:05.796816.png')
# cv2.imwrite("/home/akami-3/gitlabsource/CloudCams/code/cropped.png", img)

def get_utc_time(img_name):
    # Extract the datetime string from the filename using regex
    match = re.search(r'(\d{3})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})', img_name)

    if not match:
        raise ValueError(f"Could not extract datetime from filename: {img_name}")
    
    groups = match.groups()
    year = str(int(groups[0]) + 1800)  # Convert 225 to 2025
    observation_time_str = f"{year}-{groups[1]}-{groups[2]} {groups[3]}:{groups[4]}:{groups[5]}"
    observation_time = Time(observation_time_str, format='iso', scale='utc')
    return observation_time + 10 * u.hour


def get_initial_wcs_val(input_image_path):
    wcs_path = '/home/akami-3/gitlabsource/CloudCams/astrometrynet_files/initial.wcs'

    # get time of image wcs file is created from
    img_name = os.path.basename(input_image_path)
    initial_utc = get_utc_time(img_name)

    # get initial ra/dec from wcs file
    hdr = fits.getheader(wcs_path)
    initial_ra = hdr['CRVAL1'] * u.deg
    initial_dec = hdr['CRVAL2'] * u.deg

    return initial_utc, initial_ra, initial_dec

def recalibrate_wcs(input_image_path):
    global initial_utc, initial_ra, initial_dec

    # # mask image
    # img = crop(input_image_path)
    # cropped_path = os.path.join(os.path.dirname(input_image_path), 'cropped.jpg')
    # cv2.imwrite(cropped_path, img)

    out_dir = '/home/akami-3/gitlabsource/CloudCams/astrometrynet_files'
    solve_field_fp = '/home/akami-3/Downloads/astrometry.net-latest/astrometry.net-0.97/solver/solve-field'
    indexes_fp = '/home/akami-3/gitlabsource/CloudCams/astrometry-net-indexes'
    prefix = 'initial'
    
    none_fp = '/home/akami-3/gitlabsource/CloudCams/src/none'

    cmd = [
        solve_field_fp,
        input_image_path,
        '-o',               prefix,
        '-D',               out_dir,
        '--scale-units',    'degwidth',
        '--scale-low',      '0.1',
        '--scale-high',     '180',
        '--objs',           '2000',
        '--sigma',          '3',
        '--overwrite',
        '--index-dir',      indexes_fp,

        '-N',    'none',   # no prefix.new FITS file
        '-S',    'none',   # no prefix.solved
        '-M',    'none',   # no prefix.match
        '-R',    'none',   # no prefix.rdls
        '-i',    'none',   # no SCAMP catalog
        '-n',    'none',   # no SCAMP config snippet
        '-U',    'none',   # no prefix-indx.xyls
        '--axy', 'none',   # no augmented xylist
        '-B',    'none',   # no prefix.corr
        '-p',              # no plots
        
    ]
    
    subprocess.run(cmd, check=True)

    if os.path.exists(none_fp):
        os.remove(none_fp)

    initial_utc, initial_ra, initial_dec = get_initial_wcs_val(input_image_path)
    save_initial_wcs_values()
# img = crop('/home/akami-3/gitlabsource/CloudCams/src/Screenshot from 2025-07-29 13-44-11.png')
# cv2.imwrite('/home/akami-3/gitlabsource/CloudCams/src/Screenshot from 2025-07-29 13-44-11.png', img)
recalibrate_wcs('/home/akami-3/gitlabsource/CloudCams/src/cloudcam2250716-210610.png')
def get_center_skycoord(utc_observation_time, location):
    global initial_utc, initial_ra, initial_dec
    # Load initial wcs values
    load_initial_wcs_values()

    lst_observation_time = utc_observation_time.sidereal_time('apparent', longitude=location.lon)

    ## when reseting wcs file reset three things:
    # 1) replace initial.wcs file with a new one in astrometrynet_files
    # 2) the initial time the image used to create the wcs file was taken
    # 3) the initial ra/dec of that image from the wcs file
    initial_UTC_time_str = initial_utc.iso.split('.')[0]  # remove microseconds
    initial_time = Time(initial_UTC_time_str, format='iso', scale='utc')
    lst_initial = initial_time.sidereal_time('apparent', longitude=location.lon)

    initial_center = SkyCoord(ra=initial_ra, dec=initial_dec, frame='icrs')

    # compute how far the sky has turned
    delta_time = (lst_observation_time - lst_initial).wrap_at(24*u.hourangle)
    rotation_rate = 15.04107 * u.deg / u.hourangle
    delta_ra = (delta_time * rotation_rate).to(u.deg)

    # shift RA by that amount
    ra_new  = (initial_center.ra + delta_ra).wrap_at(360*u.deg)
    center = SkyCoord(ra=ra_new, dec=initial_center.dec, frame='icrs')
    print(f"New center RA: {center.ra.deg}, New center Dec: {center.dec.deg}")

    return center

# overwrite date and date-obs in wcs file
def repoint_wcs(wcs_path: str, utc):
    # get astropy location
    cfht_office = EarthLocation(lat=20.019547523714984 * u.deg, lon=-155.6719115353903 * u.deg, height=813.816 * u.m)
    # get center sky coord
    center = get_center_skycoord(utc, cfht_office)

    # open the WCS file for in‑place update
    with fits.open(wcs_path, mode='update') as hdul:
        hdr = hdul[0].header
        hdr['CRVAL1'] = (center.ra.deg,  'Updated RA of reference pixel')
        hdr['CRVAL2'] = (center.dec.deg, 'Updated Dec of reference pixel')

# update the date and date-obs keywords
def get_local_tle(tle_file, sat_name):
    with open(tle_file, 'r') as f:
        lines = f.readlines()
    for i in range(len(lines)):
        if lines[i].strip() == sat_name:
            return lines[i].strip(), lines[i+1].strip(), lines[i+2].strip()
    raise ValueError(f"Satellite {sat_name} not found in TLE file.")

def update_ephem(ephem_file, utc):
    eph = load('/home/akami-3/gitlabsource/CloudCams/data/de442s.bsp')
    ts  = load.timescale()
    t   = ts.from_datetime(utc.to_datetime().replace(tzinfo=timezone.utc))

    # 1) define the topos (your observing location)
    topos = wgs84.latlon(
        20.019547523714984,    # lat
       -155.6719115353903,     # lon
        elevation_m=813.816
    )
    # 2) for planets use earth+topos → ICRF for observe()
    earth = eph['earth']
    site  = earth + topos

    planet_names = [
        ('Mercury', 'MERCURY BARYCENTER'),
        ('Venus',   'VENUS BARYCENTER'),
        ('Mars',    'MARS BARYCENTER'),
        ('Jupiter', 'JUPITER BARYCENTER'),
        ('Saturn',  'SATURN BARYCENTER'),
        ('Uranus',  'URANUS BARYCENTER'),
        ('Neptune', 'NEPTUNE BARYCENTER'),
        ('Pluto',   'PLUTO BARYCENTER'),
        ('Moon',    'MOON'),
        ('Sun',     'SUN'),
    ]

    with open(ephem_file, 'w') as f:
        # — planets & Sun/Moon via .observe() —
        for label, target in planet_names:
            body        = eph[target]
            astrometric = site.at(t).observe(body).apparent()
            ra, dec, _  = astrometric.radec()
            f.write(f"{label} {ra.hours*15:.6f} {dec.degrees:.6f}\n")

        # — satellites via (satellite - topos).at() —
        tle_name, line1, line2 = get_local_tle(
            '/home/akami-3/gitlabsource/CloudCams/data/tle.txt',
            'ISS (ZARYA)'
        )
        iss = EarthSatellite(line1, line2, tle_name, ts)

        # Subtract the **Topos** (not `site`) to get a topocentric vector:
        topocentric = (iss - topos).at(t)
        ra, dec, _  = topocentric.radec()
        f.write(f"{tle_name} {ra.hours*15:.6f} {dec.degrees:.6f}\n")

def plot_overlay(plot_const_file, wcs_file, ephem_file, width, height, output_img_path, hawaiian_stars, hawaiian_lines, constellations: str, stars: str, planets: bool):
    # Verify all required files exist
    required_files = {
        'plot_const_file': plot_const_file,
        'wcs_file': wcs_file,
        'output_img_path': output_img_path
    }
    
    if planets:
        required_files['ephem_file'] = ephem_file
    if constellations == 'hawaiian':
        required_files['hawaiian_lines'] = hawaiian_lines
    if stars == 'hawaiian':
        required_files['hawaiian_stars'] = hawaiian_stars

    # Check all required files exist
    for name, filepath in required_files.items():
        if not filepath or not os.path.exists(filepath):
            print(f"Missing required file: {name} = {filepath}")
            return None

    # Check if constellations, stars, and planets are requested
    if constellations == 'none' and stars == 'none' and not planets:
        print("No constellations, stars, or planets requested. Skipping overlay.")
        return None

    # Base command that's always needed
    cmd = [
        'timeout', '120',
        plot_const_file,
        '-W', str(width),
        '-H', str(height),
        '-w', wcs_file,
        '-o', output_img_path,
        '-v'
    ]

    # Add options based on constellation type
    if constellations == '_westernconst':
        cmd.extend(['-C'])
    elif constellations == '_hawaiianconst':
        if os.path.exists(hawaiian_lines):
            cmd.extend(['-X', hawaiian_lines])
        else:
            print(f"Hawaiian constellation file not found: {hawaiian_lines}")
            return None
    elif constellations == '':
        pass
    else:
        print(f"Unknown constellation type: {constellations}. Skipping overlay.")
        return None

    # Add stars if requested
    if stars == '_westernstars':
        cmd.extend(['-B', '-j', '-b', '12'])
    elif stars == '_hawaiianstars':
        if os.path.exists(hawaiian_stars):
            cmd.extend(['-Y', hawaiian_stars])
        else:
            print(f"Hawaiian stars file not found: {hawaiian_stars}")
            return None
    elif stars == '':
        pass
    else:
        print(f"Unknown stars option: {stars}. Skipping overlay.")
        return None

    # Add planets if requested
    # planets can be _planets for True or '' for False
    if planets == '_planets':
        if os.path.exists(ephem_file):
            cmd.extend(['-U', ephem_file])
        else:
            print(f"Ephemeris file not found: {ephem_file}")
            return None
    elif planets == '':
        pass
    else:
        print(f"Unknown planets option: {planets}. Skipping overlay.")
        return None

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_img_path), exist_ok=True)

    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        print(f"Command output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print("plot-constellations stderr:")
        print(e.stderr)
        print(f"Command that failed: {' '.join(cmd)}")
        return None

# get constellation overlay
def overlay(img_path, out_dir, constellations: str, stars: str, planets: str):
    # load the background first so we know its true dimensions
    bg = cv2.imread(img_path)

    if bg is None:
        raise RuntimeError(f"Failed to read background {img_path}")

    # dynamically grab width & height
    height, width = bg.shape[:2]
    print(f"Image dimensions: {width}x{height}")

    base_img_name = os.path.basename(img_path)
    img_name = f'OVR{base_img_name}'
    utc = get_utc_time(img_name)

    wcs_file = '/home/akami-3/gitlabsource/CloudCams/astrometrynet_files/initial.wcs'
    ephem_file = '/home/akami-3/gitlabsource/CloudCams/data/ephem.cat'
    hawaiian_stars = '/home/akami-3/gitlabsource/CloudCams/data/hawaiian_const.stars'
    hawaiian_lines = '/home/akami-3/gitlabsource/CloudCams/data/hawaiian_const.lines'
    plot_const_file = '/home/akami-3/Downloads/astrometry.net-latest/astrometry.net-0.97/plot/plot-constellations'
    out_dir = out_dir

    repoint_wcs(wcs_file, utc)
    update_ephem(ephem_file, utc)

    print('header_updated')

    overlay_png_path = '/home/akami-3/gitlabsource/CloudCams/astrometrynet_files/astrometry-ngc.png'

    # plot the overlay
    if not plot_overlay(plot_const_file, wcs_file, ephem_file, width, height, overlay_png_path, hawaiian_stars, hawaiian_lines, constellations, stars, planets):
        return None
    else:
        print("Overlay plot created successfully.")

    overlay = crop(overlay_png_path)

    # put the overlay on top of the original image
    if overlay is not None:
        bg = cv2.imread(img_path)
        bg_f      = bg.astype('float32')
        overlay_f = overlay.astype('float32')

        alpha = 0.45
        beta  = 1.0 - alpha

        # 1) start with a copy of the background
        blended = bg_f.copy()

        # 2) compute a normal alpha-blend of overlay+BG
        tmp     = cv2.addWeighted(overlay_f, alpha, bg_f, beta, 0.0)

        # 3) create a mask where your overlay actually has content
        #    (e.g. any non-black pixel in overlay_f)
        mask = (overlay_f.max(axis=2) > 0)

        # 4) only replace those pixels in the background copy
        blended[mask] = tmp[mask]

        # convert back
        blended_uint8 = blended.astype('uint8')
        new_img_path = os.path.join(out_dir, img_name)
        cv2.imwrite(new_img_path, blended_uint8)

    else:
        print('Astrometry failed')

    return new_img_path

# overlay('/home/akami-3/gitlabsource/CloudCams/CloudCamImages/CloudCam250715/cloudcam2250716-010422.jpg', '/home/akami-3/gitlabsource/CloudCams/src', '_hawaiianconst', '_westernstars', '_planets')
