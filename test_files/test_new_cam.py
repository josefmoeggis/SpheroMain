# #!/usr/bin/python3
# from time import sleep
# from picamera2 import Picamera2
# from picamera2.encoders import H264Encoder
# from picamera2.outputs import FfmpegOutput
#
# picam2 = Picamera2()
# picam2.configure(picam2.create_video_configuration(main={"size": (640, 480),
#                                                          "format": "YUV420"}))
#
# # Simpler UDP output format
# output = FfmpegOutput("-f h264 udp://10.22.22.32:9000")  # Replace with your PC's IP
#
# picam2.start_recording(H264Encoder(), output=output)
#
# try:
#     while True:
#         sleep(1)
# except KeyboardInterrupt:
#     picam2.stop_recording()



#!/usr/bin/python3
from time import sleep
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
import signal
import sys

def signal_handler(sig, frame):
    """Handle clean shutdown when Ctrl+C is pressed"""
    print("Stopping camera...")
    picam2.stop_recording()
    sys.exit(0)

# Register the signal handler for clean shutdown
signal.signal(signal.SIGINT, signal_handler)

# Initialize the camera with better settings for streaming
picam2 = Picamera2()
video_config = picam2.create_video_configuration(
    main={
        "size": (640, 480),
        "format": "YUV420"
    },
    controls={
        "FrameRate": 30,  # Set to 30 fps for smoother video
        "AwbEnable": True,  # Enable auto white balance
        "AeEnable": True   # Enable auto exposure
    }
)
picam2.configure(video_config)

# Create FFmpeg output with optimized settings for network streaming
output = FfmpegOutput(
    "-f h264 "  # Use H264 format
    "-preset ultrafast "  # Use fastest encoding preset
    "-tune zerolatency "  # Optimize for low latency
    "-b:v 2M "  # Set bitrate to 2 Mbps
    "udp://YOUR_PC_IP:9000"  # Replace YOUR_PC_IP with your PC's IP address
)

# Start the camera and recording
picam2.start()
picam2.start_recording(H264Encoder(), output=output)

print("Camera streaming started. Press Ctrl+C to stop.")

# Keep the script running
try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    signal_handler(signal.SIGINT, None)