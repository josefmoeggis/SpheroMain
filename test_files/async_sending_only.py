# client.py

from flatbuffers import flexbuffers as flex
import socket
import time

HOST = "10.22.21.241"
#HOST = "127.0.0.1"
PORT = 9090


def run_tx_client(s, acc_data, rot_data, dist_data):
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



    try:

        print(packed_dict)
        # Send the packed data
        s.sendall(packed_dict)

        # Shutdown send to signal we're done sending
        #s.shutdown(socket.SHUT_WR)
        print('sending...')
        return True
    except Exception as e:
        print(f"Error unpacking response: {e}")
        return False



if __name__ == "__main__":
    rot_data = [0.5, 0.5, 0.5]
    acc_data = [0.25, 0.25, 0.25]
    dist_data = [12.0, 12.0]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            while True:
                if not run_tx_client(s, rot_data, acc_data, dist_data):
                    break
                time.sleep(1)
        except Exception as e:
            print(f"Connection error: {e}")