# client.py
from pickletools import uint8

from flatbuffers import flexbuffers as flex
import socket
import time
from sphero_sdk import SpheroRvrObserver
from sphero_sdk import RawMotorModesEnum

HOST = "10.22.22.139"
PORT = 9090

rvr = SpheroRvrObserver()
rvr.wake()

# Give RVR time to wake up
time.sleep(2)

def run_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        # Receive response
        data = b''
        while True:
            chunk = s.recv(1024)
            if not chunk:
                break
            data += chunk

        # Unpack the response
        root = flex.GetRoot(data)
        response_dict = root.Value
        # Access value as a dictionary using Value property
        left_mode = response_dict['leftMode']
        left_speed = response_dict['leftSpeed']
        right_mode = response_dict['rightMode']
        right_speed = response_dict['rightSpeed']
        servo1 = response_dict['cameraYaw']
        servo2 = response_dict['cameraPitch']
        heading_mode = response_dict['headingMode']
        speed = response_dict['speed']
        heading = response_dict['heading']
        flags = response_dict['flags']

        if heading_mode:
            rvr.drive_with_heading(speed, heading, flags)
        else:
            print('running')
            rvr.raw_motors(
                left_mode=left_mode,
                left_duty_cycle=left_speed,  # Valid duty cycle range is 0-255
                right_mode=right_mode,
                right_duty_cycle=right_speed  # Valid duty cycle range is 0-255
            )

        print(f'Right: {right_speed}, Left: {left_speed}, servo1: {servo1}, servo2: {servo2}, left_mode: {left_mode}, right_mode: {right_mode}, headingMode: {heading_mode}, speed: {speed}, heading: {heading}')

'''            except Exception as e:
            print(f"Error unpacking response: {e}")
            print(f"Raw received data: {data.hex()}")

    except Exception as e:
            print(f"Error unpacking response: {e}")'''



if __name__ == "__main__":
    while(True):
        run_client()
        time.sleep(0.01)