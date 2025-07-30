# for testing/resetting purposes

import socket
import cv2
from datetime import datetime

# save server address and port
HOST = "128.171.80.243"
PORT = 915

try:
    # create socket and connect
    with socket.create_connection((HOST, PORT)) as s:

        # send the "image" command to the server
        s.sendall(b"image\n")

        # read header line
        header = b""
        while not header.endswith(b"\n"):
            chunk = s.recv(1)
            if not chunk:
                raise ConnectionError("Connection closed before header received.")
            header += chunk

        header_text = header.decode().strip()
        print("Header:", repr(header_text))

        if not header_text.startswith(". "):
            raise ValueError(f"Unexpected header format: {header_text}")

        # get the image size in bytes
        img_size = int(header_text[2:].strip())
        print(f"Image size: {img_size} bytes")

        # read the image binary data
        image_data = b""
        while len(image_data) < img_size:
            chunk = s.recv(img_size - len(image_data))
            if not chunk:
                raise ConnectionError("Connection closed before full image was received.")
            image_data += chunk
            print(f"Received {len(image_data)} / {img_size} bytes", end="\r")

        # save to file to convert the binary data into an image
        with open("received_image.png", "wb") as f:
            f.write(image_data)

        print("\n Image successfully saved as 'received_image.png'")

        # read in image using opencv
        image = cv2.imread('received_image.png')
        # convert image to RGB color scheme
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # save the output image
        now = datetime.now()
        cv2.imwrite(f'adjusted{now}.png', rgb)

        print("\n Image successfully converted to RGB and saved as 'adjusted.png'")


except Exception as e:
    print("Error:", e)

while True:
    try:
        # wait for user inp