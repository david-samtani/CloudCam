<?php

/*
 * @author Christian Engelhardt <christian@gumdesign.com>
 * @copyright Copyright © 2009, Gum Design LLC Web Development, <http://gumdesign.com>
 * @developed for CFHT
*/

// define  page variables
define("color_theme", "blue"); // options blue 

define("page_title", "CFHT CloudCam Timelapses"); //unique page title 
define("section", "gallery"); // highlights location in nav bar
define("meta_description", ""); // unique description for the page

include("../en/includes/header.php");

?>

<?php

    // defaults
    $cam     = $_GET['cam']     ?? 'cloudcam1';
    $file    = $_GET['file']    ?? 'today';

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

    $basename    = basename($file);              // yields "cloudcam20250723.mp4"
    $prefix      = $cam;                         // e.g. "cloudcam2025"
    $currentDate = str_replace([$prefix, '.mp4'], '', $basename);

    #echo "file is $file\n";
?>

<div id="sidebar" class="grid_3">
    <div class="pad">
        <?php include("../en/includes/nav_gallery.php"); ?>
        <?php include("../en/includes/side_contact.php"); ?>
    </div>
</div>    <!-- end sidebar -->

<!-- content -->
<div class="grid_9">

<table class="overall" cellpadding=2>
  <tr>
    <td valign="top" class="sidebar" bgcolor="#0033ff"></td>
    <td bgcolor="#808080">
      <table class="overall" cellpadding=0>
        <tr colspan="2">
          <td align="center" colspan="2">
            <h3>CFHT CloudCam Timelapse Videos</h3> 
            <p>These timelapse videos are generated each morning (Hawaii Standard Time (UTC-10)),<br/>and span from sunset to sunrise.</p>
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
              <a href="timelapse2025.php?cam=cloudcam1">
              <img align="top" src="/cloudcam2/cloudcam1/cloudcam1small.jpg" width=174></a><br/><strong>East</strong></td>
            <td align="center" <?php if ($cam === 'cloudcam2') {echo 'style="background: #a9d9f5"';} ?>>
              <a href="timelapse2025.php?cam=cloudcam2">
              <img align="top" src="/cloudcam2/cloudcam2/cloudcam2small.jpg" width=174></a><br/><strong>Southwest</strong></td>
            <td align="center" <?php if ($cam === 'cloudcam2025') echo 'style="background:#a9d9f5"'; ?>>
              <a href="timelapse2025.php?cam=cloudcam2025">
              <img src="/cloudcam2/cloudcam2025/images/cloudcam2025small.jpg" width="174" alt="CloudCam 2025"></a><br/><strong>CloudCam 2025</strong></td>
          </tr>
        </table>
        </td>
      </tr>
      <tr>
       <td bgcolor="#808080">
         <p id="preview"></p>
         <video width="500" controls autoplay muted>
           <source src="<?php echo $file; ?>" type="video/mp4">Your browser does not support the video tag.
         </video>
       </td>
       <td style="border: 1px solid #FFF; vertical-align: top;" bgcolor="#808080">
        <p><strong>Click on a date below to view the timelapse video from the selected CFHT CloudCam.</strong></p>
          <pre>
            <table border="0"> 
              <?php 
              if ($cam === 'cloudcam2025') {
                exec("/usr/bin/ls cloudcam2025/images/movies/$cam* -r | head -n 7", $files, $retval);
              } else {
                exec("/usr/bin/ls movies/$cam* -r | head -n 7", $files, $retval);
              }
              foreach ($files as $file2) {
              global $fancydate;
              global $date;
              $date="";
              $fancydate="";
              exec("echo '$file2' | sed 's/.*$cam//' |sed 's/.mp4//' ", $date, $retval);
              exec("date --date $date[0]  +'%a %b %d %Y'", $fancydate, $retval);
		  
              if ($file2 === $file) {
                $bgcolor = "#a9d9f5";
              } else {
                $bgcolor = "#ececec";
              }
              
              echo "<tr><td align=\"center\" style=\"background: $bgcolor\"><a href=\"timelapse2025.php?file=$file2&cam=$cam\">$fancydate[0]</a></td></tr>";
              }?>
            </table>
          </pre>
          </td>
          </tr>
          <tr>
          <td colspan="2"  align="center">
            <p style="font-size: smaller !important">Since the timelapses start at sunset and run through to sunrise, the 
            date listed above is the date the timelapse begins.<br/>Additionally, the CloudCam may be periodically obscured by 
            inclement weather such a fog, rain, ice, or snow throughout the timelapse.</p>
            <p>The CloudCams only operate at night. If between sunset and sunrise, Hawaii Standard Time (UTC-10), 
            current images can be found on the <strong><a href="cloudcam2025/index.php?cam=<?php echo urlencode($cam); ?>">CFHT CloudCams</a></strong> page.</p>
          </td>
          </tr>
          <tr>
          <td colspan="2"  align="center">
            <p>Having trouble viewing or want to save this timelapse?<br/>Use this link to download it: 
            <strong><a href="<?php echo $file ?>" download>Download Timelapse</a></strong></p>

            <!-- If the cam is cloudcam2025, show the overlay options -->
            <?php if ($cam === 'cloudcam2025'): ?>
            <p>
            Use this link to download it with an overlay:
            <strong><a href="#" class="overlay-btn" onclick="openOverlayPopup(); return false;">
                Download Timelapse with Overlay
            </a></strong>
            </p>
            <?php endif; ?>

            <div id="overlayModal" class="modal">
              <div class="modal-content">
                <button class="close">&times;</button>
                <h2>Customize Overlay Options</h2>
                <div class="options-grid">
                  <!-- CONSTELLATIONS -->
                  <div class="option-col">
                    <h3>Constellations</h3>
                    <label><button class="circle-btn constellation-btn" data-value=""></button>None</label>
                    <label><button class="circle-btn constellation-btn" data-value="_westernconst"></button>Western</label>
                    <label><button class="circle-btn constellation-btn" data-value="_hawaiianconst"></button>Hawaiian</label>
                  </div>
                  <!-- STARS -->
                  <div class="option-col">
                    <h3>Stars</h3>
                    <label><button class="circle-btn star-btn" data-value=""></button>None</label>
                    <label><button class="circle-btn star-btn" data-value="_westernstars"></button>Western</label>
                    <label><button class="circle-btn star-btn" data-value="_hawaiianstars"></button>Hawaiian</label>
                  </div>
                  <!-- PLANETS -->
                  <div class="option-col">
                    <h3>Planets</h3>
                    <label><button class="circle-btn planet-btn" data-value=""></button>Off</label>
                    <label><button class="circle-btn planet-btn" data-value="_planets"></button>On</label>
                  </div>
                </div>
                <div id="statusMessage" class="status"></div>
                <button id="generateBtn" class="download-btn">Download</button>
              </div>
            </div>

            <style>
              .modal { display:none; position:fixed; top:0;left:0;width:100%;height:100%;
                       background:rgba(0,0,0,0.5); align-items:center;justify-content:center; }
              .modal-content { background:#fff; padding:20px; border-radius:8px;
                               width:80vmin; max-width:500px; position:relative; }
              .close { position:absolute; top:10px; right:10px; background:#eee; border:none;
                       font-size:18px; width:30px; height:30px; border-radius:50%; cursor:pointer; }
              .options-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:15px; margin:20px 0; }
              .option-col h3 { margin-bottom:8px; font-size:1rem; }
              .option-col label { display:flex; align-items:center; margin-bottom:6px; cursor:pointer; }
              .circle-btn { width:16px; height:16px; border:2px solid #0033ff; border-radius:50%;
                            margin-right:8px; background:#fff; transition:background-color .2s; }
              .circle-btn.selected { background:#0033ff; }
              .download-btn { display:block; margin:0 auto; padding:8px 16px; font-size:1rem; }
              .status { text-align:center; margin-bottom:10px; font-style:italic; }
            </style>
          </td>
        </tr>
      <tr>
       <td colspan="2"  align="center">
         <p>More information about our CloudCams can be found on the <strong><a href="about.php">About the CloudCams</a></strong> page.</p>
            <p style="font-size: smaller !important"><strong>CloudCam Timelapse Videos Copyright &#169; 2022-<span id="CurrentYear"></span> Canada France Hawaii Telescope Corporation.</strong><br/>
    Permission is granted to copy, distribute and/or modify these videos under the terms of the <strong>GNU Free Documentation License</strong>,<br/>
    Version 1.3, or any later version, published by the Free Software Foundation.
    A copy of the license can be found <a href="https://www.gnu.org/licenses/fdl-1.3.html">here</a>.<br/>
    For inquiries, contact info@cfht.hawaii.edu</p>
       </td>
      </tr>
      
   </table>
  </td>
</tr>
</table>
    <!-- end edit content -->
</div>
<div class="clear"></div>
<!-- end content wrapper-->
<?php include("../en/includes/footer.php"); ?>


<!-- moved JS so table remains valid HTML -->
<script>
  let modal = document.getElementById('overlayModal');
  let closeBtn = modal.querySelector('.close');
  let statusMessage = document.getElementById('statusMessage');
  let generateBtn = document.getElementById('generateBtn');
  let isGenerating = false;
  let currentDate = "<?= $currentDate ?>";

  let selectedValues = { constellation:'', star:'', planet:'' };

  function handleButtonClick(button, category) {
    document.querySelectorAll(`.${category}-btn`).forEach(b=>b.classList.remove('selected'));
    button.classList.add('selected');
    selectedValues[category] = button.dataset.value;
  }

  document.querySelectorAll('.constellation-btn').forEach(b=>b.onclick=()=>handleButtonClick(b,'constellation'));
  document.querySelectorAll('.star-btn').forEach(b=>b.onclick=()=>handleButtonClick(b,'star'));
  document.querySelectorAll('.planet-btn').forEach(b=>b.onclick=()=>handleButtonClick(b,'planet'));

  function resetButtons() {
    document.querySelectorAll('.circle-btn').forEach(b=>b.classList.remove('selected'));
    selectedValues = { constellation:'', star:'', planet:'' };
    statusMessage.textContent = '';
  }

  function openOverlayPopup() {
    modal.style.display = 'flex';
    resetButtons();
  }

  closeBtn.onclick = () => {
    if (isGenerating) {
      isGenerating = false;
      statusMessage.textContent = 'Overlay generation canceled';
    } else {
      modal.style.display = 'none';
      resetButtons();
    }
  };

  window.onclick = e => {
    if (e.target==modal) {
      if (isGenerating) {
        isGenerating = false;
        statusMessage.textContent = 'Overlay generation canceled';
      } else {
        modal.style.display = 'none';
        resetButtons();
      }
    }
  };

  document.addEventListener('keydown', e => {
    if (e.key==='Escape') {
      if (isGenerating) {
        isGenerating = false;
        statusMessage.textContent = 'Overlay generation canceled';
      } else {
        modal.style.display = 'none';
        resetButtons();
      }
    }
  });

  generateBtn.onclick = async () => {
    // block all‑none/off
    if (
      selectedValues.constellation==='' &&
      selectedValues.star==='' &&
      selectedValues.planet===''
    ) {
      alert('Please select at least one overlay option. To download raw timelapse, use the "Download" link below the video.');
      return;
    }

    isGenerating = true;
    generateBtn.disabled = true;
    statusMessage.textContent = 'Generating movie...';

    try {
      // Call your FastAPI endpoint instead of the PHP one
      await fetch('http://localhost:8000/generate-overlay/', {
        method: 'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({
          // FastAPI will invoke timelapse_with_overlay for us
          constellations: selectedValues.constellation,
          stars:          selectedValues.star,
          planets:        selectedValues.planet,
          date:           currentDate
        })
      });
      // get the URL
      // poll for “exists”
      const url = '/cloudcam2/cloudcam2025/images/requested_overlay_movie.mp4';
      while (true) {
        // bust any browser/CDN cache
        const resp = await fetch(url + '?_=' + Date.now(), { method: 'HEAD' });
        if (resp.ok) break;
        await new Promise(r => setTimeout(r, 1000));
      }

      if (isGenerating) {
        let link = document.createElement('a');
        link.href = '/cloudcam2/cloudcam2025/images/requested_overlay_movie.mp4';
        link.download = 'timelapse_with_overlay.mp4';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        statusMessage.textContent = 'Download complete!';
      }
    } catch(err) {
      alert('Error generating overlay: '+err);
    } finally {
      isGenerating = false;
      generateBtn.disabled = false;
    }
  };
</script>

<!-- Year Update Script-->
<script type="text/javascript">
function CurrentYear () {   
var fulldate = new Date();
var year = fulldate.getFullYear();
document.getElementById("CurrentYear").innerHTML = (year); 
}
CurrentYear(); 
</script>
