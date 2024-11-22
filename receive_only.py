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
time.sleep(2)  # Give RVR time to wake up

def run_robot(response_dict):
    try:
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
            print('true')
        else:
            rvr.raw_motors(
                left_mode=left_mode,
                left_duty_cycle=left_speed,
                right_mode=right_mode,
                right_duty_cycle=right_speed
            )

        print(f'Right: {right_speed}, Left: {left_speed}, servo1: {servo1}, servo2: {servo2}, '
              f'left_mode: {left_mode}, right_mode: {right_mode}, headingMode: {heading_mode}, '
              f'speed: {speed}, heading: {heading}')

    except Exception as e:
        print(f"Error processing command: {e}")

def run_rx_client(socket_connection):
    try:
        buffer = b''
        while True:
            try:
                chunk = socket_connection.recv(1024)
                if not chunk:
                    return None
                buffer += chunk

                # Process complete messages
                if len(buffer) >= 4:  # Min størrlse msg
                    root = flex.GetRoot(buffer)
                    response_dict = root.Value
                    print(response_dict)
                    # this is where the process was run if failure with modification
                    buffer = b''
                    return response_dict

            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error receiving data: {e}")
                return None

    except Exception as e:
        print(f"Connection error: {e}")
        return None

if __name__ == "__main__":
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.settimeout(0.1)
            while True:
                    run_data = run_rx_client(s)
                    run_robot(run_data)
    except KeyboardInterrupt:
        print("\nShutting down client...")