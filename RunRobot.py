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

def process_command(data):
    try:
        print('waiting to receive data...')
        root = flex.GetRoot(data)
        response_dict = root.Value

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
                left_mode=uint8(left_mode),
                left_duty_cycle=uint8(left_speed),
                right_mode=right_mode,
                right_duty_cycle=right_speed
            )

        print(f'Right: {right_speed}, Left: {left_speed}, servo1: {servo1}, servo2: {servo2}, '
              f'left_mode: {left_mode}, right_mode: {right_mode}, headingMode: {heading_mode}, '
              f'speed: {speed}, heading: {heading}')

    except Exception as e:
        print(f"Error processing command: {e}")

def run_tx_client(acc_data, rot_data, dist_data):
    builder = flex.Builder()
    # Pack
    with builder.Map():
        builder.Key('acc')
        builder.TypedVectorFromElements(acc_data, flex.Type.FLOAT)

        builder.Key('rot')
        builder.TypedVectorFromElements(rot_data, flex.Type.FLOAT)

        builder.Key('dist')
        builder.TypedVectorFromElements(dist_data, flex.Type.FLOAT)

    packed_dict = builder.Finish()


    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))

            # Send the packed data
            s.sendall(packed_dict)

            # Shutdown send to signal we're done sending
            s.shutdown(socket.SHUT_WR)

        except Exception as e:
            print(f"Error unpacking response: {e}")


def run_client():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

            # Set a timeout to avoid hanging
            s.settimeout(0.1)

            buffer = b''
            while True:
                print('waiting to send data...')
                try:
                    chunk = s.recv(1024)
                    if not chunk:
                        break
                    buffer += chunk

                    # Process complete messages
                    if len(buffer) >= 4:  # Min størrlse msg
                        process_command(buffer)
                        buffer = b''

                except socket.timeout:
                    # No data received, continue listening
                    continue
                except Exception as e:
                    print(f"Error receiving data: {e}")
                    break

    except Exception as e:
        print(f"Connection error: {e}")
        time.sleep(1)  # Wait before retrying connection

if __name__ == "__main__":
    rot_data = [0.5, 0.5, 0.5]
    acc_data = [0.25, 0.25, 0.25]
    dist_data = [12.0, 12.0]
    try:
        while True:
            run_client()
            run_tx_client(acc_data, rot_data, dist_data)

    except KeyboardInterrupt:
        print("\nShutting down client...")