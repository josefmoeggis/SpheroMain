from flatbuffers import flexbuffers as flex
import socket
import asyncio

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



async def run_robot(response_dict, rvr):
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
            await rvr.drive_with_heading(speed, heading, flags)
        else:
            await rvr.raw_motors(
                left_mode=left_mode,
                left_duty_cycle=left_speed,
                right_mode=right_mode,
                right_duty_cycle=right_speed
            )

    except Exception as e:
        print(f"Error processing command: {e}")



async def run_rx_client(rvr, host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.setblocking(True)
            await asyncio.sleep(.1)
            while True:

                buffer = b''
                while True:
                    try:
                        chunk = s.recv(1024)
                        if not chunk:
                            break
                        buffer += chunk

                        if len(buffer) >= 4:  # Min størrelse msg
                            root = flex.GetRoot(buffer)
                            response_dict = root.Value

                            buffer = b''
                            await run_robot(response_dict, rvr)
                            await asyncio.sleep(0.02)
                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"Error receiving data: {e}")
                        break
                await asyncio.sleep(0.03)
    except Exception as e:
        print(f"Connection error: {e}")
        await asyncio.sleep(1)  # Wait before retrying connection