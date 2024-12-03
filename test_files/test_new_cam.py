#!/usr/bin/python3
from time import sleep

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480),
                                                         "format": "YUV420"}))
picam2.start_recording(H264Encoder(), output=FfmpegOutput("-f rtp udp://127.0.0.1:9000"))