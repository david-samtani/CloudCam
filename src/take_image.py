import socket
import cv2
from datetime import datetime
import os
import auto_brightness

def capture_image(out_dir):
    # save server address and port
    HOST = "128.171.80.243"
    PORT = 915

    # etimes = [10, 15, 20, 30, 45, 60]
    # gains = [10, 50, 100, 150, 200, 300]

    # create socket and connect
    with socket.create_connection((HOST, PORT)) as s:
        s.sendall(('etime').encode() + b'\n')
        etime_resp = s.recv(1024).decode()
        curr_etime = float(etime_resp.strip().split()[-1])
        print(f'current etime: {curr_etime}')

        s.sendall(('gain').encode() + b'\n')
        gain_resp = s.recv(1024).decode()
        curr_gain = float(gain_resp.strip().split()[-1])
        print(f'current gain: {curr_gain}')

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

        print("\n Image successfully saved'")

        # read in image using opencv
        image = cv2.imread('received_image.png')
        # convert image to RGB color scheme
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # get date for timestamp
        now = datetime.now()
        timestamp = now.strftime("%m%d-%H%M%S")

        # save the output image
        output_name = f'cloudcam225{timestamp}.jpg'
        output_path = os.path.join(out_dir, output_name)
        cv2.imwrite(output_path, rgb)
        print("\n Image successfully saved")

        # adjust etime and gain of camera
        new_etime, new_gain = auto_brightness.adjust_brightness(rgb, curr_etime, curr_gain)

        s.sendall((f'etime {new_etime}').encode() + b'\n')
        etime_resp = s.recv(1024).decode()
        new_etime = etime_resp.strip().split()[-1]
        print(f'new etime: {new_etime}')

        s.sendall((f'gain {new_gain}').encode() + b'\n')
        gain_resp = s.recv(1024).decode()
        new_gain = gain_resp.strip().split()[-1]
        print(f'new gain: {new_gain}')

        return output_path
        