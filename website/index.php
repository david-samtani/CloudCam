<?php 

/*
 * @author Christian Engelhardt <christian@gumdesign.com>
 * @copyright Copyright © 2009, Gum Design LLC Web Development, <http://gumdesign.com>
 * @developed for CFHT
*/

// define  page variables
define("color_theme", "blue"); // options blue 

define("page_title", "CFHT Cloudcams"); //unique page title 
define("section", "gallery"); // highlights location in nav bar
define("meta_description", ""); // unique description for the page

include("../en/includes/header.php"); 

?>

<?php
    // defaults
    $cam     = $_GET['cam']     ?? 'cloudcam1';
    $constellations = $_GET['constellations'] ?? 'none';
    $stars = $_GET['stars'] ?? 'none';
    $planets = $_GET['planets'] ?? 'off';
    $file    = $_GET['file']    ?? 'today';

    // Sanity checks
    if (!in_array($cam, ['cloudcam1','cloudcam2','cloudcam2025'], true)) { $cam = 'cloudcam1'; }
    if (!in_array($constellations, ['none','western','hawaiian'], true))       { $constellations = 'none'; }
    if (!in_array($stars, ['none','western','hawaiian'], true))       { $stars = 'none'; }
    if (!in_array($planets, ['on','off'], true))           { $planets = 'off'; }


    # file selection
    if ($file === 'today') {
        $out = [];
        if ($cam !== 'cloudcam2025') {
            exec("ls -r movies/{$cam}* 2>/dev/null | head -n 1", $out, $ret);
        } else {
            exec("ls -r cloudcam2025/images/movies/{$cam}* 2>/dev/null | head -n 1", $out, $ret);
        }
        $file = $out[0] ?? '';
    }

    #echo "file is $file\n";
?>

<META HTTP-EQUIV="Refresh"
      CONTENT="60; URL=index.php?cam=<?php echo urlencode($cam); ?>&constellations=<?php echo urlencode($constellations); ?>&stars=<?php echo urlencode($stars); ?>&planets=<?php echo urlencode($planets); ?>">

<div id="sidebar" class="grid_3">
<div class="pad">
	<?php include("../en/includes/nav_gallery.php"); ?>
	<?php include("../en/includes/side_contact.php"); ?>
</div>
</div>	

<!-- end sidebar -->

<!-- content -->
<div class="grid_9">
<!-- edit content -->
 
<?php
if ($cam !== 'cloudcam2025') {
    # default image path
    $imagePath = "/cloudcam2/$cam/$cam.jpg";
} else {
    # Build image suffix based on combinations
    $suffixes = [
        'constellations' => [
            'none' => '',
            'western' => '_westernconst',
            'hawaiian' => '_hawaiianconst'
        ],
        'stars' => [
            'none' => '',
            'western' => '_westernstars',
            'hawaiian' => '_hawaiianstars'
        ],
        'planets' => [
            'off' => '',
            'on' => '_planets'
        ]
    ];

    # put name together
    $prefix  = 'cloudcam2025';
    $suffix  = $suffixes['constellations'][$constellations]
             . $suffixes['stars'][$stars]
             . $suffixes['planets'][$planets];

    if ($suffix === '') { $suffix = '_raw'; }

    $imagePath = "/cloudcam2/cloudcam2025/images/{$prefix}{$suffix}.jpg";
}

?>

<table class="overall" cellpadding=2>
  <tr>
    <td valign="top" class="sidebar" bgcolor="#0033ff"></td>
    <td bgcolor="#808080">
      <table class="overall" cellpadding=0>
        <tr colspan="2">
          <td align="center" colspan="2">
	    <h3>CFHT CloudCam Images</h3> 
	    <p><strong>CFHT CloudCams are highly specialized cameras designed to image the night sky.<br/>As a result, 
	    they only operate between sunset and sunrise, Hawaii Standard Time (UTC-10).</strong></p>
	    <p>When operational, images on this page update every 60 seconds.<br/>The page will automatically refresh when a new image is available.</p>
	    <p>Weather data updates every 10 seconds, 24 hours a day.</p>
         </td>
       </tr>
       <tr>
         <td align="center" colspan="2">
         <!-- *** UNCOMMENT OUT THIS SECTION TO INCLUDE A NOTICE ON THE PAGE ***
	 <p><strong>Notice<br/>[[ADD DATE HERE]]</strong></p>
	 <p>[[ADD NOTICE TEXT HERE]].</p> 
         -->
         </td>
       </tr>
       <tr>
        <td  align="center" colspan="2">
        <table class="overallBorderless">
          <tr>
            <td align="center" <?php if ($cam === 'cloudcam1') {echo 'style="background: #a9d9f5"';} ?>>
              <a href="index.php?cam=cloudcam1">
              <img align="top" src="/cloudcam2/cloudcam1/cloudcam1small.jpg" width=174></a><br/><strong>East</strong></td>
            <td align="center" <?php if ($cam === 'cloudcam2') {echo 'style="background: #a9d9f5"';} ?>>
              <a href="index.php?cam=cloudcam2">
              <img align="top" src="/cloudcam2/cloudcam2/cloudcam2small.jpg" width=174></a><br/><strong>Southwest</strong></td>
            <td align="center" <?php if ($cam === 'cloudcam2025') {echo 'style="background:#a9d9f5"';} ?>>
              <a href="index.php?cam=cloudcam2025&constellations=<?php echo urlencode($constellations); ?>&stars=<?php echo urlencode($stars); ?>&planets=<?php echo urlencode($planets); ?>">
              <img src="/cloudcam2/cloudcam2025/images/cloudcam2025small.jpg" width="174" alt="CloudCam 2025">
              </a><br/><strong>CloudCam 2025</strong></td>
          </tr>
     </table>
     </td>
  </tr>

  <tr>
   <td bgcolor="#808080" >
   <img src="<?php echo htmlspecialchars($imagePath); ?>" width="640" alt="CloudCam image">
   </td>
  </tr>

    <!-- mode dropdowns -->
  <?php if ($cam === 'cloudcam2025'): ?>
  <tr>
    <td align="center" colspan="2">
        <div style="margin:10px 0;">

        <!-- Constellations dropdown -->
        <form method="get" style="display:inline-block; margin-right:20px;">
            <input type="hidden" name="cam" value="cloudcam2025">
            <input type="hidden" name="stars" value="<?php echo htmlspecialchars($stars); ?>">
            <input type="hidden" name="planets" value="<?php echo htmlspecialchars($planets); ?>">
            <label for="constellationsSelect"><strong>Constellations:</strong></label>
            <select id="constellationsSelect" name="constellations" onchange="this.form.submit()">
            <option value="none" <?php if ($constellations==='none') echo 'selected'; ?>>None</option>
            <option value="western" <?php if ($constellations==='western') echo 'selected'; ?>>Western</option>
            <option value="hawaiian" <?php if ($constellations==='hawaiian') echo 'selected'; ?>>Hawaiian</option>
            </select>
        </form>
        <!-- Stars dropdown -->
        <form method="get" style="display:inline-block; margin-right:20px;">
            <input type="hidden" name="cam" value="cloudcam2025">
            <input type="hidden" name="constellations" value="<?php echo htmlspecialchars($constellations); ?>">
            <input type="hidden" name="planets" value="<?php echo htmlspecialchars($planets); ?>">
            <label for="starsSelect"><strong>Stars:</strong></label>
            <select id="starsSelect" name="stars" onchange="this.form.submit()">
            <option value="none" <?php if ($stars==='none') echo 'selected'; ?>>None</option>
            <option value="western" <?php if ($stars==='western') echo 'selected'; ?>>Western</option>
            <option value="hawaiian" <?php if ($stars==='hawaiian') echo 'selected'; ?>>Hawaiian</option>
            </select>
        </form>
        <!-- Planets toggle button -->
        <form method="get" style="display:inline-block; margin-right:20px;">
            <input type="hidden" name="cam" value="cloudcam2025">
            <input type="hidden" name="constellations" value="<?php echo htmlspecialchars($constellations); ?>">
            <input type="hidden" name="stars" value="<?php echo htmlspecialchars($stars); ?>">
            <label for="planetsSelect"><strong>Planets:</strong></label>
            <select id="planetsSelect" name="planets" onchange="this.form.submit()">
            <option value="off" <?php if ($planets==='off') echo 'selected'; ?>>Off</option>
            <option value="on" <?php if ($planets==='on') echo 'selected'; ?>>On</option>
            </select>
        </form>
        </div>
    </td>
    </tr>
    <?php endif; ?>
    
  <tr>
   <td>

  <iframe src="/webcam/weather/WeatherInfo/WeatherInfo.html" width=640px height=180px> 
    </iframe>    
  
    <?php
       #$output = shell_exec('/cfht/bin/dl_gemini');
       #echo "<pre>$output</pre>";
    ?>
   
   </td>
  </tr>
  <tr>
   <td  align="center"> <p style="font-size: smaller !important">As noted above, these cameras only operate between sunset and sunrise, 
   Hawaii Standard Time (UTC-10).<br/>If the image above displays <strong>"Daytime (cloudcam sleeping)"</strong>, they are not operational. 
   <br/>When operational, these cameras may be periodically obscured by inclement weather such a fog, rain, ice, or snow.</p>
   <p>Images from these cameras are used to create nightly timelapse videos.<br/>These videos can be found on the 
   <a href="../timelapse2025.php?cam=<?php echo urlencode($cam); ?>"><strong>CFHT CloudCam Timelapses</strong></a> page.</p>
   </td>
  </tr>
   
  <tr>
   <td align="center">
   <p><strong>Is it daytime in Hawai'i and the CloudCams are sleeping? Check out our summit webcams!</strong><br/>
   While not optimized for imaging the night sky, our webcams operate 24 hours a day. <br/>
   Find them on the <strong><a href="../webcams.php">CFHT Webcams</a></strong> page.</p>
   <p><strong>Also available is our StarCam, a 4K 24/7 video livestream!</strong><br/>This stream is available through Youtube
   and provides a view of the western sky day and night.<br/>Find it on the <strong><a href="../starcam.php">CFHT-Asahi StarCam</a></strong> page.</p>
   </td>
  </tr>
   <tr>
       <td colspan="2"  align="center">
         <p>More information about our CloudCams can be found on the <strong><a href="about.php">About the CloudCams</a></strong> page.</p>
         <p style="font-size: smaller !important"><strong>CloudCam Images Copyright &#169; <span id="CurrentYear"></span> Canada France Hawaii Telescope Corporation.</strong><br/>
    Permission is granted to copy, distribute and/or modify these images under the terms of the <strong>GNU Free Documentation License</strong>,<br/>
    Version 1.3, or any later version, published by the Free Software Foundation.
    A copy of the license can be found <a href="https://www.gnu.org/licenses/fdl-1.3.html">here</a>.<br/>
    For inquiries, contact info@cfht.hawaii.edu</p>
       </td>
      </tr>
</table>

<!-- end edit content -->	
</div>
<div class="clear"></div>
</div><!-- end content wrapper-->
<?php include("../en/includes/footer.php"); ?>

<!-- Year Update Script-->
<script type="text/javascript">
function CurrentYear () {   
var fulldate = new Date();
var year = fulldate.getFullYear();
document.getElementById("CurrentYear").innerHTML = (year); 
}
CurrentYear(); 
</script>