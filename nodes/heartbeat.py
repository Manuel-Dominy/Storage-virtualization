import socket
import json
import time
import sys


MASTER_HOST = "127.0.0.1"
MASTER_PORT = 6000


if len(sys.argv) != 2:

    print("Usage:")
    print("python heartbeat.py <node_number>")

    sys.exit()

print(sys.argv)
node_number = sys.argv[1]


NODE_ID = f"Node {node_number}"


NODE_PORTS = {

    "1": 5001,

    "2": 5002,

    "3": 5003

}


NODE_PORT = NODE_PORTS[node_number]


def send_message(message):

    client = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    client.settimeout(5)

    client.connect(
        (MASTER_HOST, MASTER_PORT)
    )

    client.send(
        json.dumps(message).encode()
    )

    response = client.recv(4096).decode()

    client.close()

    return response


# --------------------------------
# REGISTER NODE
# --------------------------------

registration = {

    "type": "REGISTER_NODE",

    "node_id": NODE_ID,

    "host": "127.0.0.1",

    "port": NODE_PORT

}


try:

    response = send_message(registration)

    print(
        f"{NODE_ID} registered with Master"
    )


except Exception as error:

    print(
        "Could not connect to Master:",
        error
    )

    sys.exit()


# --------------------------------
# SEND HEARTBEATS
# --------------------------------

while True:

    heartbeat = {

        "type": "HEARTBEAT",

        "node_id": NODE_ID

    }


    try:

        send_message(heartbeat)

        print(
            f"{NODE_ID} → HEARTBEAT"
        )


    except Exception as error:

        print(
            f"{NODE_ID} → Master unavailable"
        )


    time.sleep(3)