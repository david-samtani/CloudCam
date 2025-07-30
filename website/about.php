<?php 

/*
 * @author Christian Engelhardt <christian@gumdesign.com>
 * @copyright Copyright © 2009, Gum Design LLC Web Development, <http://gumdesign.com>
 * @developed for CFHT
*/

// define  page variables
define("color_theme", "blue"); // options blue 
define("page_title", "About the CFHT CloudCams"); //unique page title 
define("section", "gallery"); // highlights location in nav bar
define("meta_description", ""); // unique description for the page

include("../en/includes/header.php"); 

?>
<?php if (!isset($_GET['file'])) {$_GET['file'] = 'today';}
      if (!isset($_GET['cam'])) {$_GET['cam'] = 'cloudcam1';}

?>

<div id="sidebar" class="grid_3">
<div class="pad">
	<?php include("../en/includes/nav_gallery.php"); ?>
	<?php include("../en/includes/side_contact.php"); ?>
</div>
</div>	<!-- end sidebar -->

<!-- content -->
<div class="grid_9">
<!-- edit content -->
<table class="overall" cellpadding=2><tr><td valign="top" class="sidebar" bgcolor="#0033ff">
<td bgcolor="#808080">
<table class="overall" cellpadding=0>
  <tr colspan="2">
     <td align="center" colspan="2">
<h3>About the CFHT Cloudcams</h3>
     </td>
  </tr>
  <tr>
   <td colspan="2">
<p>The Cloud Cameras (known colloquially as “CloudCams”) of Canada-France-Hawaii 
Telescope are a pair 
of cameras mounted along the exterior catwalk of the observatory. These cameras were once standard 
consumer-grade DSLR cameras, but they have since been extensively modified for very high sensitivity 
and converted to autonomous computer control. From their weathertight enclosures, these cameras are 
capable of taking images of clouds (their namesake!), along with other weather and human activity—
additionally, even the incandescence of volcanic eruptions and the faint glow of the Milky Way can be 
seen! Much of this is visible on the brightest moonlit night or the darkest moonless night as the cameras 
automatically adapt and optimize for the best possible images regardless of the ambient light conditions. 
Due to the extreme sensitivity of these cameras, they only operate during the nighttime hours from sunset 
to sunrise. </p>

<h4>What you are seeing</h4>
<p>
The two CloudCams mounted at CFHT are strategically located around the catwalk to observe specific 
areas, with the name of each camera and its field of view identified on the map included with this text. 
</p>
<img src="Scaled_Map.png" width="650">
<p>
CloudCam1 faces nearly due east and includes the city of Hilo and it’s environs north along the Hamakua 
Coast and south towards Puna. Also visible are ships on the ocean, aircraft utilizing Hilo International 
Airport, and vehicles climbing Saddle Road. As this camera faces east, stars and planets all appear to 
rise from this direction—over the course of the night an object that appears on the horizon, will rise higher 
and higher before leaving the image at the top of the frame.
</p>
<p>
CloudCam2 faces southwest with a view of CFHT’s neighbour observatories along Maunakea’s East 
Ridge and down into the Saddle between Maunakea and Maunaloa. Lights from the US Army’s 
Pohakuloa Training Area can occasionally be seen in addition to a faint glow of city lights from Kailua-
Kona which is hidden from direct view by the slopes of Maunaloa and Hualalai. This camera also has 
spectacular views of the beautiful southern sky. In summer months the Milky Way dazzles, arching high 
over Maunaloa, with the Hawaiian constellation of<em> Hanaiakamalama</em> — more famously known as Crux or 
the Southern Cross—visible as well. 
</p>
<p>
Lastly, though Maunakea is one of the driest sites in the entire Pacific Ocean, and sits above the vast 
majority of weather, storms occasionally do reach the summit. During these events, which occur most 
often during the rainy season of November to April, it is possible that some or all of the CloudCams will 
have their views partially or completely obscured by fog, ice or snow. As a result, CFHT cannot guarantee 
that the CloudCams will be fully operational during these times. 
</p>
<h4>Wait? Is that an alien?! </h4>
<p>
Because of the extreme sensitivity of these camera, even very faint things in the sky can appear very 
bright. The Moon looks a lot like the sun and the planets appear brighter than we are used to seeing 
them. Even a crescent moon is so bright it saturates the image like the sun does to normal cameras. You 
can usually tell the difference because when the moon rises you will still see stars but when the sun rises 
all the stars disappear. Remember: everything in the sky rises and sets at a different time each day! What 
was visible the night before, may not be visible at the same time the next night. 
</p>
<h4>About the time-lapse videos</h4>
<p>
The CloudCams take a picture about every 30 seconds and, at the end of the night, compiles them into a  
time-lapse ‘Night Movie’. These movies compress an entire night into about a minute of footage—
everything in the movies appears greatly accelerated. For example, airplanes may appear as streaks and 
ships and cars may appear to move quite quickly.</p>

<p>These timelapses can be found on the <a href="timelapse.php"><strong>CFHT CloudCam Timelapses</strong></a> page.</p>

<h4>Location</h4>
<p>
These cameras are located on the Canada-France-Hawai-Telescope on Maunakea:
19.8253° N, 155.4696° W altitude: 4,204 meters  </p> 
   </td>
  </tr>
                    <tr>
                        <td colspan="2">
                          <p>As noted above, the CloudCams only operate at night. If between sunset and sunrise, Hawaii Standard Time (UTC-10), 
         current images can be found on the <strong><a href="index.php">CFHT CloudCams</a></strong> page.</p>
                        </td>
                    </tr>

</table>
</table>


<!-- end edit content -->	
</div>
<div class="clear"></div>
</div><!-- end content wrapper-->
<?php include("../en/includes/footer.php"); ?>