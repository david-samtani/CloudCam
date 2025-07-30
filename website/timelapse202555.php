<?php
// timelapse2025.php

// Handle AJAX calls before rendering the rest of the page
if (isset($_GET['action'])) {
    header('Content-Type: application/json');

    // 1a) Kick off the Python process
    if ($_GET['action'] === 'execute-overlay' && $_SERVER['REQUEST_METHOD'] === 'POST') {
        $payload = json_decode(file_get_contents('php://input'), true);
        if (empty($payload['command'])) {
            http_response_code(400);
            echo json_encode(['error'=>'Missing command']);
            exit;
        }
        // fire-and-forget
        exec(sprintf(
            "%s > /dev/null 2>&1 &",
            $payload['command']
        ));
        echo json_encode(['status'=>'started']);
        exit;
    }

    // Poll for file’s existence
    if ($_GET['action'] === 'check-file' && $_SERVER['REQUEST_METHOD'] === 'GET') {
        // path where your Python script will drop the movie
        $path = '/data/cloudcams/cloudcam2025/images/requested_overlay_movie.mp4';
        echo json_encode(['exists'=> file_exists($path) ]);
        exit;
    }

    // unknown action
    http_response_code(400);
    echo json_encode(['error'=>'Unknown action']);
    exit;
}
?>

<?php
/*
 * @author Christian Engelhardt <christian@gumdesign.com>
 * @copyright Copyright © 2009, Gum Design LLC Web Development
 * @developed for CFHT
*/

// define page variables
define("color_theme", "blue");
define("page_title", "CFHT CloudCam Timelapses");
define("section", "gallery");
define("meta_description", "");

include("../en/includes/header.php");
?>

<?php
    // defaults
    $cam  = $_GET['cam']  ?? 'cloudcam1';
    $file = $_GET['file'] ?? 'today';

    // file selection
    if ($file === 'today') {
        $out = [];
        if ($cam !== 'cloudcam2025') {
            exec("ls -r movies/{$cam}* 2>/dev/null | head -n 1", $out, $ret);
        } else {
            exec("ls -r cloudcam2025/images/movies/{$cam}* 2>/dev/null | head -n 1", $out, $ret);
        }
        $file = $out[0] ?? '';
    }

    $basename    = basename($file);
    $prefix      = $cam;
    $currentDate = str_replace([$prefix, '.mp4'], '', $basename);
?>

<div id="sidebar" class="grid_3">
  <div class="pad">
    <?php include("../en/includes/nav_gallery.php"); ?>
    <?php include("../en/includes/side_contact.php"); ?>
  </div>
</div><!-- end sidebar -->

<div class="grid_9"><!-- content wrapper -->

<table class="overall" cellpadding=2>
  <tr>
    <td valign="top" class="sidebar" bgcolor="#0033ff"></td>
    <td bgcolor="#808080">
      <table class="overall" cellpadding=0>
        <tr colspan="2">
          <td align="center" colspan="2">
            <h3>CFHT CloudCam Timelapse Videos</h3>
            <p>These timelapse videos are generated each morning (HST UTC‑10) from sunset to sunrise.</p>
          </td>
        </tr>
        <tr>
          <td align="center" colspan="2">
            <!-- Optional notice here -->
          </td>
        </tr>
        <tr>
          <td align="center" colspan="2">
            <table class="overallBorderless">
              <tr>
                <td align="center" <?= $cam==='cloudcam1'? 'style="background:#a9d9f5"':'' ?>>
                  <a href="timelapse2025.php?cam=cloudcam1">
                    <img src="/cloudcam2/cloudcam1/cloudcam1small.jpg" width=174 alt="East">
                  </a><br/><strong>East</strong>
                </td>
                <td align="center" <?= $cam==='cloudcam2'? 'style="background:#a9d9f5"':'' ?>>
                  <a href="timelapse2025.php?cam=cloudcam2">
                    <img src="/cloudcam2/cloudcam2/cloudcam2small.jpg" width=174 alt="Southwest">
                  </a><br/><strong>Southwest</strong>
                </td>
                <td align="center" <?= $cam==='cloudcam2025'? 'style="background:#a9d9f5"':'' ?>>
                  <a href="timelapse2025.php?cam=cloudcam2025">
                    <img src="/cloudcam2/cloudcam2025/images/cloudcam2025small.jpg" width=174 alt="CloudCam 2025">
                  </a><br/><strong>CloudCam 2025</strong>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <tr>
          <td bgcolor="#808080">
            <video width="500" controls autoplay muted>
              <source src="<?= htmlspecialchars($file) ?>" type="video/mp4">
              Your browser does not support the video tag.
            </video>
          </td>
          <td style="border:1px solid #FFF;vertical-align:top;" bgcolor="#808080">
            <p><strong>Click a date to view that timelapse.</strong></p>
            <pre><table border="0">
<?php
  if ($cam==='cloudcam2025') {
    exec("/usr/bin/ls cloudcam2025/images/movies/{$cam}* -r | head -n 7", $files, $retval);
  } else {
    exec("/usr/bin/ls movies/{$cam}* -r | head -n 7", $files, $retval);
  }
  foreach ($files as $file2) {
    $d=[]; $f=[];
    exec("echo '$file2' | sed 's/.*$cam//' | sed 's/.mp4//'", $d, $r1);
    exec("date --date {$d[0]} +'%a %b %d %Y'", $f, $r2);
    $bg = $file2===$file ? '#a9d9f5' : '#ececec';
    echo "<tr><td align=\"center\" style=\"background:$bg\">
            <a href=\"timelapse2025.php?file=$file2&cam=$cam\">{$f[0]}</a>
          </td></tr>\n";
  }
?>
            </table></pre>
          </td>
        </tr>

        <!-- overlay trigger + modal -->
        <tr>
          <td colspan="2" align="center">
            <button onclick="openOverlayPopup()" class="overlay-btn">
              Download Timelapse with Overlay
            </button>

            <div id="overlayModal" class="modal">
              <div class="modal-content">
                <button class="close">&times;</button>
                <h2>Customize Overlay Options</h2>
                <div class="options-grid">
                  <!-- CONSTELLATIONS -->
                  <div class="option-col">
                    <h3>Constellations</h3>
                    <label><button class="circle-btn constellation-btn" data-value="none"></button>None</label>
                    <label><button class="circle-btn constellation-btn" data-value="western"></button>Western</label>
                    <label><button class="circle-btn constellation-btn" data-value="hawaiian"></button>Hawaiian</label>
                  </div>
                  <!-- STARS -->
                  <div class="option-col">
                    <h3>Stars</h3>
                    <label><button class="circle-btn star-btn" data-value="none"></button>None</label>
                    <label><button class="circle-btn star-btn" data-value="western"></button>Western</label>
                    <label><button class="circle-btn star-btn" data-value="hawaiian"></button>Hawaiian</label>
                  </div>
                  <!-- PLANETS -->
                  <div class="option-col">
                    <h3>Planets</h3>
                    <label><button class="circle-btn planet-btn" data-value="off"></button>Off</label>
                    <label><button class="circle-btn planet-btn" data-value="on"></button>On</label>
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

        <!-- ... your footer rows here ... -->

      </table>
    </td>
  </tr>
</table>

</div><!-- end content wrapper -->
<div class="clear"></div>

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
    // require one per column
    if (!selectedValues.constellation || !selectedValues.star || !selectedValues.planet) {
      alert('Please make a selection in each category');
      return;
    }
    // block all‑none/off
    if (
      selectedValues.constellation==='none' &&
      selectedValues.star==='none' &&
      selectedValues.planet==='off'
    ) {
      alert('Please select at least one overlay option. To download raw timelapse, use the "Download" link below the video.');
      return;
    }

    isGenerating = true;
    generateBtn.disabled = true;
    statusMessage.textContent = 'Generating movie...';

    try {
      await fetch('timelapse2025.php?action=execute-overlay', {
        method: 'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({
          command: `python3 -c "import sys; sys.path.insert(0,'/home/...'); from timelapse_overlay import timelapse_with_overlay; timelapse_with_overlay('${selectedValues.constellation}','${selectedValues.star}','${selectedValues.planet}','${currentDate}')"`
        })
      });
      while (isGenerating) {
        let resp = await fetch('timelapse2025.php?action=check-file');
        let data = await resp.json();
        if (data.exists) break;
        await new Promise(r=>setTimeout(r,1000));
      }
      if (isGenerating) {
        let link = document.createElement('a');
        link.href = 'cloudcam2025/images/requested_overlay_movie.mp4';
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

<!-- Year Update Script -->
<script>
  function CurrentYear(){
    document.getElementById("CurrentYear").textContent = new Date().getFullYear();
  }
  CurrentYear();
</script>
