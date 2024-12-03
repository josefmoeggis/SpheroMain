#!/usr/bin/python3
from time import sleep
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480),
                                                         "format": "YUV420"}))

# Use specific FFmpeg options to match the receiver
output = FfmpegOutput("-f rtp -sdp_file video.sdp rtp://127.0.0.1:9000")

picam2.start_recording(H264Encoder(), output=output)

try:
    while True:
        sleep(1)  # Keep the script running
except KeyboardInterrupt:
    picam2.stop_recording()