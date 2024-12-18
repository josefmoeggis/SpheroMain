from pickletools import uint8

from flatbuffers import flexbuffers as flex
import socket
import asyncio
import time
import numpy as np

# Just for building flexbuffer msg
async def pack_data(rot_data, acc_data, dist_data):
    builder = flex.Builder()
    try:
        with builder.Map():
            builder.Key('acc')
            builder.TypedVectorFromElements(acc_data, flex.Type.FLOAT)
            builder.Key('rot')
            builder.TypedVectorFromElements(rot_data, flex.Type.FLOAT)
            builder.Key('dist')
            builder.TypedVectorFromElements(dist_data, flex.Type.FLOAT)


        return builder.Finish()
    except Exception as e:
        print('Error in packing data')
        print(e)


# Running RVR
async def run_robot(vertical_servo, response_dict, rvr):
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

        #print('LeftMode: '+ left_mode + ' RightMode: '+ right_mode + ' leftSpeed: ' + left_speed + 'rightSpeed: ' + right_speed)

        if heading_mode:
            await rvr.drive_with_heading(speed, heading, flags)
        else:
            await rvr.raw_motors(
                left_mode=left_mode,
                left_duty_cycle=left_speed,
                right_mode=right_mode,
                right_duty_cycle=right_speed
            )

        vertical_servo.move_servo_position(0, servo2)

    except Exception as e:
        print(f"Error processing command: {e}")


async def receive_with_timeout(socket, timeout=1.0):
    try:
        # Convert the blocking socket receive to an async operation
        chunk = await asyncio.wait_for(
            asyncio.get_event_loop().sock_recv(socket, 1024),
            timeout=timeout
        )
        return chunk
    except asyncio.TimeoutError:
        return None


# Only exported function to run_robot
async def run_rx_client(v_servo, rvr, host, port):
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.setblocking(False)
                await asyncio.sleep(.1)
                while True:

                    buffer = b''
                    while True:
                        try:
                            chunk = await receive_with_timeout(s, .1)
                            if chunk is None:
                                continue
                            if not chunk:
                                break

                            buffer += chunk

                            if len(buffer) >= 4:  # Min størrelse msg
                                root = flex.GetRoot(buffer)
                                response_dict = root.Value

                                buffer = b''
                                await run_robot(v_servo, response_dict, rvr)
                                await asyncio.sleep(0.02)
                        except (ConnectionResetError, ConnectionAbortedError) as e:
                            print(f"Connection lost: {e}")
                            break  # Break inner loop to trigger reconnection
                        except Exception as e:
                            print(f"Error processing data: {e}")
                            break  # Break inner loop on any other error
        except (ConnectionRefusedError, socket.error) as e:
            print(f"Connection failed: {e}, retrying in 1 second...")
            await asyncio.sleep(1)  # Wait before retrying connection
        except Exception as e:
            print(f"Unexpected error: {e}, retrying in 1 second...")
            await asyncio.sleep(1) # Wait before retrying connection