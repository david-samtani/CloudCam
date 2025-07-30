import os
from pathlib import Path
import astrometry
import automated_process

def iterate_images(start_directory, end_directory):
    # Supported image extensions
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    
    # Check if directories exist
    if not os.path.exists(start_directory):
        print(f"Start directory {start_directory} does not exist")
        return
    if not os.path.exists(end_directory):
        print(f"End directory {end_directory} does not exist")
        return
    
    # Iterate through all files in start directory
    for file in os.listdir(start_directory):
        if file.endswith(image_extensions):
            # Create full path by joining start directory and filename
            file_path = os.path.join(start_directory, file)
            print(f"Found image: {file_path}")
            astrometry.overlay(file_path, end_directory, True, True)
            # automated_process.add_caption(file_path, end_directory)
            # You can process the image file here
            
if __name__ == "__main__":
    # Replace with your directory paths
    start_directory = "/home/akami-3/gitlabsource/CloudCams/good"
    end_directory = "/home/akami-3/gitlabsource/CloudCams/hawaiian"
    iterate_images(start_directory, end_directory)
