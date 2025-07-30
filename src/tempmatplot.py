# for resetting wcs file purposes

import sys
from PIL import Image
import matplotlib.pyplot as plt

def show_image(path):
    img = Image.open(path)
    plt.figure(figsize=(8, 6))
    plt.imshow(img)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def main():
    show_image('/home/akami-3/gitlabsource/CloudCams/code/adjusted2025-07-08 09:29:05.796816.png')

if __name__ == "__main__":
    main()
