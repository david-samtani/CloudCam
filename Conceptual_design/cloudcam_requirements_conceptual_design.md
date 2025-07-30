# Cloud Camera requirements and conceptual design

## Background

The existing cloud cams continue to provide the desired functionality however they are becoming increasingly unreliable, requiring frequent power cycling.  The cameras used are consumer grade DSLRs that have been significantly modified for the purpose of the CloudCams and are impractical to repair/replace beyond sourcing an entirely new camera.

Until recently, one of the limitations of COTs cameras aimed at the amateur astronomy market was that they used small, low resolution sensors, or that the larger sensors were costly (multi k$).  Furthermore, the raw output from sensors, especially older CCDs, is frequently unsuitable as a displayable data product without additional processing due to sensor artifacts.  Consumer grade photographic cameras employ internal processing to produce images that require minimal post-processing by the consumer to achieve a usable image.
Consequently, the existing cloud cams use modified DSLRs to achieve high resolution and sensitivity in the red ([overview](https://info.cfht.hawaii.edu/display/ccam/Cloud+Camera), [detailed description](https://info.cfht.hawaii.edu/display/ccam/Cloudcam+Description), [Specifications](https://info.cfht.hawaii.edu/display/ccam/Cloudcam+Specifications)).

Newer CMOS sensors approach the sensitivity of CCDs and exhibit far less artifacts so the images are generally usable with no or minimal post-processing.  Cameras intended for astronomical use are available off-the-shelf in which the IR blocking filter, typically installed on consumer cameras, is not present.  At the same time, much larger formats are available at modest cost compared to what was possible when the original cloud cameras were conceived in 2013/2014.  In the case of CMOS, these are universally electronically shuttered devices that avoid the need of a mechanical shutter that will quickly fail due to the large number of actuations required over a timescale of years.  These cameras are commonly sold without the near IR filter installed on consumer photographic cameras, so they require no modification for optimal use in astronomy.

Another important aspect that has been made a requirement for the refurbishment is that control and image acquisition of the camera should be through a standard interface that is exposed through a linux compatible API.  No consumer grade photographic camera provides this feature.

### Comparison of any proposed concept against the existing camera

Unfortunately it is difficult to compare the existing DSLR camera against industrial/amateur-astronomy cameras because the sensitivity metrics provided are incompatible.  This is exacerbated by the post-processing that happens internally on the DSLR cameras.  Consequently, establishment of a meaningful comparison of a proposed sensor/camera/optics combination without testing the equipment is not practical or resource efficient given the cost of the cameras one might consider using.  The most popular CMOS sensors being used are made by Sony, and the read noise (controlled by the specific camera implementation) and QE are within a factor of two of the best that can be expected from a scientific grade sensor, in other words likely to exceed the effective SNR of the existing DSLR.

Consequently, there is no sensitivity requirement specifically called out.

***
## Requirements

The basic requirements of the cloud cams are as follows:

### Optical
1. The field of view of the camera along the horizontal axis shall be between 50 and 100 degrees (TBD).  This has been increased over that of the existing Cloudcam, 57x40 degrees, as an option to provide a wider field.
2. The true resolution shall be equivalent to a minimum of 2Mp, with a goal of 8Mp.  At 2Mp, the image resolution must be sensor resolution limited.
3. The images produced should be in color and sensitive to the NIR (no IR cut filter)
4. Focus shall be fixed and optimized at 0 Celcius.
5. The lens/camera combination will be tested for "general sensitivity and image quality" before proceeding with final design (see comment above).
6. The optical mount shall allow interchangeability of fixed focus lenses within the same lens series.

### Camera and Sun-shutter
7. The camera and lens combination must make use of commonly available equipment requiring minimal and preferably no modification.
8. A shutterless sensor shall be used.
9. A slow-speed "sun-shutter" (heretofore, the shutter) shall be installed to block the sun from the camera sensor during daytime.
10. The shutter shall include switches to positively detect the open and closed states.
11. The shutter shall have an MTBF of no less than 10 years. 
12. The camera shall use a standard hardware interface (e.g. USB/Ethernet) for control and image acquisition with no need for custom electronics, implementing a linux compatible API.
13. Goal: The shutter should close when power is not present.
14. A software failsafe shall be implemented in that the shutter will close if an excessive amount of saturated pixels are detected in the image.

### Power, Housing & Mechanical
15. The enclosure shall not be significantly larger than the existing CloudCam enclosure.
16. A means to remotely power cycle the entire camera unit, including any control computer must be provided.
17. The camera housing shall be IP65 rated
18. Goal: The housing window shall be coated to minimize ghost images.  Alternatively, an uncoated window shall be tested to determine if the ghosts are accecptable.  It is expected that the image quality will primarily be degraded by the window cleanliness and any moisture present, so it is questionable whether this is a relevant requirement.
19. The housing window (at minimum) shall be heatable to a temperature of 10 C at least.
20. A thermal fuse sensing the ambient air temperature of the enclosure shall be provided for any heater.
21. The housing shall contain at least one temperature sensor, sensing the air temperature within the housing.
22. The housing shall not be significantly larger than the existing cloud camera housing.
23. A means to orient the camera so that the long image axis is corresponds to the horizon direction shall be provided.
24. The CloudCam shall be powered from one of the building UPS circuits.

### Operational
25. The image cadence shall match the existing cloud camera cadence of at least one image per three minutes.
26. The mechanical shutter must operate, notably for closure prior to sunrise, in the absence of a network connection. 
27. Status of critical system conditions shall be reported in the status server.  These shall include:
  * Shutter open/close state 
  * System power state
  * Window/housing heater state
  * Controller/embedded-computer ethernet connectivity state
  * System state string, intelligibly describing any error/warning states.
26. The system shall access one or more status server variables to determine whether it should operate.
29. A simple interface shall be provided to observers to block operation of the cameras.
30. Operation of the window/housing heater shall be autonomous, based on the local temperature and weather data gathered from the status server.
31. Minimal human interaction should be necessary to recover from software errors.
32. A logging mechanism shall be provided to record key events (e.g. software/driver restarts, reloads).
33. A schedule for cleaning the glass on the cameras shall be put in place and observed (frequency TBD).

### Data product
34. The data product should be photo-realistic and free of common detector artifacts.
35. Any post-processing shall not inhibit the image cadence.
36. Photometric accuracy/calibration is not required, the goal is a "photogenic" image.
37. Subjectively, cloud contrast shall match that of the existing cameras.

***
## Proposed Solution

### Imaging sensor/camera: ZWO ASI294MC
ZWO brand cameras now have heritage in a few CFHT projects, having been used for the shutterwell camera, the temporary visible camera replacement in the original ASIVA (installed in 2020), and now the ASIVA replacement, [Nana ao](https://gitlab.cfht.hawaii.edu/instrumentation/nana-ao).  No significant post-processing is currently being applied to the images obtained with these as they are completely satisfactory for their intended use, which is likely to be the case given what is needed for the cloud cameras.

The ZWO ASI294MC, color camera, operated in default 2x2 binning mode, provides a resolution of 4144x2822 resolution (11.7 Mp).  Pixels are effectively 4.64x4.64 microns in size.  The ASI1294MC uses an IMX294 backside illuminated sensor.  This is a micro-4/3 format sensor, which  is the largest sensor format supported by current industrial machine vision type lenses.  Read noise is approximately 2 electrons, with 14 bit ADC sampling.  Note that it is difficult to obtain similar specifications for consumer photographic cameras as the heavy post-processing makes it difficult to compare with cameras that provide a raw digitized image output.  However, we anticipate that the sensitivity will exceed that of the current cameras based on the use of backside illuminated sensor, the high throughput of its Bayer color filters, and the ability to bin - which is uncommon in color sensors.

#### Cooling option
A significant improvement in SNR *may* be obtained with the cooled version of this camera for 30 second long exposures.  TBD whether this requirement justifies the added issue of the heating inside the cloudcam enclosure, or how to sink heat out of the enclosure.  The increase in cost is not significant (~$300).  It is possible the dark count is lower than the sky background, in which case the improvement in SNR will be modest; this estimate is still TBD.  As an alternative, the cooled camera could be purchased with the option of disabling or significantly reducing the cooling if issues are noted.  Also, problems may arise with condensation on the CCD window under certain conditions.

***
### Optics
The IMX492LQJ sensor used in the ZWO ASI294MC recommends that the optics be no faster than f/2.8 and have an exit pupil distance of no less than 100 mm.  Deviating from these requirements affects the sensitivity of the sensor because the lenslets used on the CMOS device will not focus the light incident on the lenslet into the photosensitive region of the pixel.  Meeting these requirements becomes challenging for wider field of view lenses.

The lens imaging performance should be based on the binned pixel size of 9.28 microns, which implies a Nyquist limit spatial frequency of 54 lines/mm.  Two lens series were identified meeting most of our criteria; the LM**XC lenses by Kowa and the Dimension lenses by Zeiss.  The Zeiss Dimension series is now discontinued with no replacement to fill its use-niche.  The following table summarizes the key characteristics of these lenses:

![Lens comparison table (Confluence)](https://info.cfht.hawaii.edu/pages/viewpageattachments.action?pageId=171282755&sortBy=date&highlight=OM-system_7-14mm_f2p8_PRO_MTF-chart.png&highlight=CloudCam+lens+comparisons.png&&preview=/171282755/171282760/CloudCam%20lens%20comparisons.png)

The only lens that approaches the telecentricity requirement for the IMX492 sensor is the Zowa LM8XC.  The sensitivity losses are impossible to determine without actually testing the lenses with the sensor.  The MTF performance of the Zeiss lenses is marginally better, however the non-telecentricity is worse than the Kowa lenses - also since these are discontinued, discussion about these is mostly for the purpose of comparison.

Another option to consider is the use of an micro-4/3 (MFT) consumer grade photographic lens.  These have the advantage of having a large flange focal distance of 19.25 mm which is fixed by the MFT standard. Also, the price/performance ratio can be expected to be higher than for industrial lenses.  The exit pupil is not typically specified on such lenses as the manufacturer ensures suitability of their lens designs for their proprietary camera sensors.  One possibility would be the OM system (Olympus) 7-14mm zoom f/2.8 PRO lens.  We have access to this lens and it could be tested for its suitability.  The MTF graph for this lens looks promising, similar in performance to the Kowa lens although only the MTF for 60 cycles/mm is provided: ![OM-system 7-14mm f/2.8 Pro MTF chart (Confluence)](https://info.cfht.hawaii.edu/pages/viewpageattachments.action?pageId=171282755&sortBy=date&highlight=OM-system_7-14mm_f2p8_PRO_MTF-chart.png&highlight=CloudCam+lens+comparisons.png&&preview=/171282755/171282759/OM-system_7-14mm_f2p8_PRO_MTF-chart.png). Panasonic/Leica also major MFT lens producers, some Leica options are given below. 

#### Other possibilities include:

* M.Zuiko Digital ED 12mm f/2.0: ![MTF chart](https://info.cfht.hawaii.edu/pages/viewpageattachments.action?pageId=171282755&preview=/171282755/171282770/M.-Zuiko-Digital-12mm-f2_MTF_Average.png)

* M.Zuiko Digital ED 8mm f/1.8 Fisheye PRO OM, stopped down as needed - but this is a 180 degree f.o.v. lens!: ![MTF chart](https://info.cfht.hawaii.edu/pages/viewpageattachments.action?pageId=171282755&preview=/171282755/171282771/Olympus_8mm_f_1_8_MTF.jpg)

* Leica 8-18mm f/2.8 (107 degree f.o.v. at wide angle): ![MTF chart](https://info.cfht.hawaii.edu/pages/viewpageattachments.action?pageId=171282755&preview=/171282755/171282772/Leica_H-E08018_MTF-chart.jpg)

* Leica 12mm f/1.4 H-X012, stopped down as needed (84 degree f.o.v.): ![MTF chart](https://info.cfht.hawaii.edu/pages/viewpageattachments.action?pageId=171282755&preview=/171282755/171282773/Leica_H-X012_04_MTF.jpg)    

*It should be emphasized that the image quality will ultimately largely be dependent on the state of cleanliness of the enclosure window, so one shouldn't get too bogged down in MTF numbers obtained under ideal conditions - the field of view and mechanical stability of the lens are probably more important factors.*

#### Window
Edmund optics offers a 75mm diameter hydrophobic visible AR coated, outdoor-rated borosilicate window (#36-073) that meets the aperature requirements for these lenses.

#### Baffling
Some means to prevent stray light from entering around the opening between the lens and the camera will have to be devised.

***
### Control & RPC
An rPi will be used to capture images from the camera, as we do for the shutterwell and Nana ao cameras.  The detailed implementation is still TBD and may not be exactly as implemented on these systems, for example, the fits-stream approach used by Tom Vermeulen for the Spirou guider may be used instead.

The rPi will also control power relays for the window/housing heater and shutter.  One or more DC power supplies are anticipated to power the relays.  The simplest way to implement power cycling of the cloudcams is to power cycle both together through a common AC line run to an RPC in the computer room. 

***
### Shutter

All three lenses proposed have 13mm of backfocus, which would allow for a relatively small shutter with short stroke to be interposed between the lens and the CCD camera (TBC).  The LMxxXC lenses have an output aperture of 23 mm, so a simple single-leaf shutter would require a stroke of ~25mm.  Typically, we would require ~365 actuation cycles per year, or ~3600 actuations over the 10 year MTBF period in the requirements. 

##### Rotary solenoid concept
The shutter would consist of a rotating plate with an aperature, or simply a balanced shutter arm connected to a continuous duty rotary solenoid.  When power is removed from the solenoid, the built-in return spring will close the shutter.  This significantly reduces the likelihood of the shutter failing in the open state and largely removes the possibility of the shutter not closing when power is absent.

A quick drawing of the possible mechanical layout for the shutter indicates that a 30 degree rotary solenoid would be sufficient (the holding torque for a 30 degree solenoid is higher than for a 45 degree device).  A Ledex 30-degree solenoid designed for 14V nominal operation was tested down to 8 V opening voltage using an APW hit-and-hold solenoid driver that drops the holding voltage to 50% of the actuating voltage.  The holding power operated at this voltage is only 0.9 W, which has no impact in terms of additional heat generated while the shutter is open.  The torque will be far sufficient to operate a light-weight shutter.  The MTBF for these solenoids is typically between 1-5 million cycles.

##### Linear actuator concept
The mightyZAP 12L-35S-22 micro linear actuator has 28mm of stroke, 70 N force and internal limit switches to define the motion limits.  These are sufficiently inexpensive that they may be tested for MTBF in-house.  This motor operates on 12VDC nominal, 2.2A (26W).  A DPDT relay for motion reversal would be required.  Optionally, a second power kill relay could be included to remove power entirely from the actuator rather than entirely use the limit switches for this purpose.

This concept is not preferred because the shutter will not close unless power is present and it is commanded to close.  It is also more complicated mechanically.  Its advantage is that it can be scaled to a very large aperture fairly simply, for example if the entire lens opening had to be blocked off.

#### Applicable to both concepts above
Inductive/capacitive proximity switches will be used to positively identify opening and closing of the shutter.  Sensing the closed state is particularly critical as failure to close indicates that someone should cover the camera.  The solenoids will be driven by a solenoid driver board that reduces the actuating voltage to 50% or less of the actuating voltage to minimize heat dissipation with the shutter in the open state.

The shutter leaf should not be blackened, but left highly reflective to minimize solar heating.

***
### Focus
Typically, C-mount lenses have a built-in lockable focus ring.  In my experience these are often difficult to adjust.  Depending on what is found, fine-focus may be provided using a lockable manual optical stage moving either the lens or camera.

***
### Temperature sensing
A single BME-280 sensor will be interfaced to the rPi to provide temperature, pressure and humidity of the air in the enclosure.  

***
### Regular cleaning
Some consideration should be given to the ease of opening the enclosure as cleaning the front glass may occasionally (once a year?) involve accessing the surface inside the enclosure.  Hardened hygrophobic coatings may be considered, especially for the outfacing surface.  A cleaning of the outside surface every two weeks and after every major storm could be considered.

***
### Cost estimate
| **Item**                             | **Part number**        | **Manufacturer (supplier)** | **Qty.** | **Unit cost** | **Ext. cost** | **Comments**                                                          |
|--------------------------------------|:----------------------:|:---------------------------:|:--------:|--------------:|--------------:|-----------------------------------------------------------------------|
| Camera/sensor                        | ZWO ASI-294MC (cooled) | ZWO (High Point Scientific) | 1 | $999      | $999.00   |                                                                                      |
| Cabinet window                       | 34-528                 | Edmund Optics               | 1 | $100.00   | $100.00   | 80-40 scratch/dig borosilicate glass, hygrophobic AR coated, not tested for optical quality                 |
| Rotary solenoid                      | 810-282-330            | Ledex-JE (Newark)           | 1 | $61.97    | $61.97    | This is a nominal 14V continuous duty solenoid, will test for operability at 12V     |
| Micro 4/3" lens 20 MP                | LM8XC                  | Kowa (RMA Electronics)      | 1 | $1,186.00 | $1,186.00 |                                                                                      |
| Enclosure 12x8x6", IP65, 304 SS      | N.A.                   | Vevor (Amazon)              | 1 | $61.99    | $61.99    | Same series of cabinets as used on Nana-ao, Exact size TBD                           |
| Control computer                     | Raspberry Pi 5         | (Amazon)                    | 1 | $70.95    | $70.95    |                                                                                      |
| rPi PCIe M.2 HAT                     | X1001                  | Geekworm (Amazon)           | 1 | $12.90    | $12.90    | (TBD) may not be needed, also we may opt to use the bottom mount board               |
| NVMe solid state drive               | WD_BLACK 250GB SN770   | Western Digital (Amazon)    | 1 | $39.99    | $39.99    | (TBD) may not be needed                                                              |
| 4-relay, 4-input rPi HAT             | SM-I-010               | Sequent Microsystems        | 1 | $45.00    | $45.00    | For proximity switches and driving shutter solenoid  & heater                        |
| 12VDC power supply (DIN) - 60W       | S8VK-G06012            | Omron (Digikey)             | 1 | $74.76    | $74.76    | Will supply both the shutter and the heater - this avoids high voltages near the rPi |
| Proximity sensor - 4mm sensing dist. | E2B-M12KS04-M1-B2      | Omron (Digikey)             | 2 | $28.38    | $56.76    |                                                                                      |
| Proximity sensor cable               | XS2F-M12PVC4A2M        | Omron (Digikey)             | 2 | $16.33    | $32.66    |                                                                                      |
| BME-280 sensor                       | 381                    | Adafruit                    | 1 | $14.95    | $14.95    | Supplies temperature, pressure and humidity                                          |
| Breaker, 2A, B trip-curve            | 1019909                | Phoenix Contact (Digikey)   | 1 | $15.71    | $15.71    | Heater power supply protection                                                       |
| Breaker, 1A, B-trip-curve            | 1011962                | Phoenix Contact (Digikey)   | 2 | $15.71    | $31.42    | For 120VAC input and solenoid                                                        |
| Linear fine translation stage        | SEMX80                 | Keenso (Amazon)             | 1 | $70.66    | $70.66    |                                                                                      |
| Other materials                      | N.A.                   | N.A.                        | 1 | $600.00   | $600.00   | Metal stock, power resistors, thermal switch, connectors, etc.                       |

**TOTAL: $3475 **