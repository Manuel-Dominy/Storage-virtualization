import socket
import json
import threading
import time
import os


# ==================================================
# NODE 2 CONFIGURATION
# ==================================================

NODE_ID = "Node 2"

NODE_HOST = "127.0.0.1"
NODE_PORT = 5002

MASTER_HOST = "127.0.0.1"
MASTER_PORT = 6000

HEARTBEAT_INTERVAL = 3

STORAGE_FOLDER = r"D:\DistributedFileSystem\storage\node2"


# ==================================================
# CREATE STORAGE FOLDER
# ==================================================

os.makedirs(
    STORAGE_FOLDER,
    exist_ok=True
)


# ==================================================
# SEND MESSAGE TO MASTER
# ==================================================

def send_to_master(message):

    client = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    client.settimeout(5)

    try:

        client.connect(
            (
                MASTER_HOST,
                MASTER_PORT
            )
        )

        client.send(
            json.dumps(message).encode()
        )

        response = client.recv(
            4096
        ).decode()

        return response

    except Exception:

        return None

    finally:

        client.close()


# ==================================================
# REGISTER NODE
# ==================================================

def register_with_master():

    registration = {

        "type":
            "REGISTER_NODE",

        "node_id":
            NODE_ID,

        "host":
            NODE_HOST,

        "port":
            NODE_PORT

    }


    while True:

        response = send_to_master(
            registration
        )


        if response:

            print(
                f"✓ {NODE_ID} registered with Master"
            )

            return


        print(
            f"⚠ {NODE_ID}: "
            "Master unavailable."
        )

        print(
            "  Retrying registration..."
        )

        time.sleep(5)


# ==================================================
# HEARTBEAT
# ==================================================

def heartbeat_loop():

    while True:

        heartbeat = {

            "type":
                "HEARTBEAT",

            "node_id":
                NODE_ID

        }


        response = send_to_master(
            heartbeat
        )


        if response:

            print(
                f"♥ {NODE_ID} → HEARTBEAT"
            )

        else:

            print(
                f"⚠ {NODE_ID} → "
                "Master unavailable"
            )


        time.sleep(
            HEARTBEAT_INTERVAL
        )


# ==================================================
# HANDLE CLIENT
# ==================================================

def handle_client(
    connection,
    address
):

    try:

        print()
        print(
            f"Connection received from {address}"
        )


        file_name = connection.recv(
            1024
        ).decode()


        if not file_name:

            return


        print(
            f"Receiving: {file_name}"
        )


        connection.send(
            "READY".encode()
        )


        file_path = os.path.join(
            STORAGE_FOLDER,
            file_name
        )


        with open(
            file_path,
            "wb"
        ) as file:

            while True:

                data = connection.recv(
                    4096
                )


                if not data:

                    break


                file.write(
                    data
                )


        print(
            "✓ File/block stored successfully!"
        )

        print(
            f"  Location: {file_path}"
        )


    except Exception as error:

        print(
            "❌ File transfer error:",
            error
        )


    finally:

        connection.close()


# ==================================================
# STORAGE SERVER
# ==================================================

def storage_server():

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )


    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )


    server.bind(
        (
            NODE_HOST,
            NODE_PORT
        )
    )


    server.listen(10)


    print()
    print(
        f"{NODE_ID} storage server running..."
    )

    print(
        f"Listening on "
        f"{NODE_HOST}:{NODE_PORT}"
    )


    while True:

        connection, address = server.accept()


        thread = threading.Thread(
            target=handle_client,
            args=(
                connection,
                address
            )
        )


        thread.start()


# ==================================================
# START NODE
# ==================================================

print()
print("========================================")
print("              NODE 2")
print("========================================")

print(
    f"Node ID: {NODE_ID}"
)

print(
    f"Storage: {STORAGE_FOLDER}"
)

print()


register_with_master()


heartbeat_thread = threading.Thread(
    target=heartbeat_loop,
    daemon=True
)

heartbeat_thread.start()


storage_server()