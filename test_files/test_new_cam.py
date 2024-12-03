#!/usr/bin/python3
from time import sleep
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480),
                                                         "format": "YUV420"}))

# Configure H264 encoder with specific parameters
encoder = H264Encoder(bitrate=1000000, repeat=True, iperiod=15)

# More robust FFmpeg output command
output = FfmpegOutput(
    "-f h264 "
    "-vcodec copy "  # Copy the encoded stream without re-encoding
    "-tune zerolatency "  # Minimize latency
    "-preset ultrafast "
    "udp://10.22.46.50:9000"  # Your PC's IP
)

picam2.start_recording(encoder, output=output)

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    picam2.stop_recording()