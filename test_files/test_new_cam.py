#!/usr/bin/python3
from time import sleep
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480),
                                                         "format": "YUV420"}))

# Simpler UDP output format
output = FfmpegOutput("-f h264 udp://10.22.22.32:9000")  # Replace with your PC's IP

picam2.start_recording(H264Encoder(), output=output)

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    picam2.stop_recording()