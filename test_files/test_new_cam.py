#!/usr/bin/python3
from time import sleep
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FfmpegOutput

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))

# Configure MJPEG output
encoder = MJPEGEncoder(bitrate=10000000)
output = FfmpegOutput(
    f"-f mpjpeg -r 30 udp://10.22.46.50:9000"  # Replace with your PC's IP
)

picam2.start_recording(encoder, output=output)

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    picam2.stop_recording()