import socket
import json
import os


# ==================================================
# CONFIGURATION
# ==================================================

FILE_PATH = r"D:\DistributedFileSystem\test_files\sample.txt"

BLOCK_FOLDER = r"D:\DistributedFileSystem\file_processing\blocks"

BLOCK_SIZE = 20

MASTER_HOST = "127.0.0.1"
MASTER_PORT = 6000


# ==================================================
# SPLIT FILE
# ==================================================

def split_file():

    os.makedirs(
        BLOCK_FOLDER,
        exist_ok=True
    )

    # Remove old blocks

    for file_name in os.listdir(BLOCK_FOLDER):

        file_path = os.path.join(
            BLOCK_FOLDER,
            file_name
        )

        if os.path.isfile(file_path):

            os.remove(file_path)


    print()
    print("Splitting file...")
    print()


    with open(
        FILE_PATH,
        "rb"
    ) as file:

        block_number = 1


        while True:

            data = file.read(
                BLOCK_SIZE
            )


            if not data:

                break


            block_name = (
                f"block_{block_number:03d}.dat"
            )


            block_path = os.path.join(
                BLOCK_FOLDER,
                block_name
            )


            with open(
                block_path,
                "wb"
            ) as block_file:

                block_file.write(data)


            print(
                f"Created: {block_name}"
            )


            block_number += 1


    print()
    print("File splitting completed.")


# ==================================================
# ASK MASTER FOR BLOCK PLACEMENT
# ==================================================

def get_block_placement(block_name):

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


        message = {

            "type":
                "GET_BLOCK_PLACEMENT",

            "block_name":
                block_name

        }


        client.send(
            json.dumps(
                message
            ).encode()
        )


        response_data = client.recv(
            4096
        ).decode()


        response = json.loads(
            response_data
        )


        return response


    except Exception as error:

        print()
        print(
            "❌ Could not contact Master"
        )

        print(
            "Reason:",
            error
        )

        return None


    finally:

        client.close()


# ==================================================
# SEND BLOCK TO NODE
# ==================================================

def send_block(
    block_path,
    node
):

    block_name = os.path.basename(
        block_path
    )

    node_id = node["node_id"]

    node_host = node["host"]

    node_port = node["port"]


    print(
        f"    Sending {block_name} "
        f"→ {node_id}"
    )


    client = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    client.settimeout(5)


    try:

        client.connect(
            (
                node_host,
                node_port
            )
        )


        # ------------------------------------------
        # Send block filename
        # ------------------------------------------

        client.send(
            block_name.encode()
        )


        # ------------------------------------------
        # Wait for READY
        # ------------------------------------------

        response = client.recv(
            1024
        ).decode()


        if response != "READY":

            print(
                f"    ❌ {node_id} "
                "did not accept block"
            )

            return False


        # ------------------------------------------
        # Send block data
        # ------------------------------------------

        with open(
            block_path,
            "rb"
        ) as file:

            while True:

                data = file.read(
                    4096
                )


                if not data:

                    break


                client.send(
                    data
                )


        print(
            f"    ✓ {block_name} "
            f"stored on {node_id}"
        )


        return True


    except Exception as error:

        print(
            f"    ❌ Failed → {node_id}"
        )

        print(
            f"       Reason: {error}"
        )

        return False


    finally:

        client.close()


# ==================================================
# MAIN UPLOAD PROCESS
# ==================================================

print()
print("========================================")
print("       DISTRIBUTED FILE UPLOAD")
print("       MASTER CONTROLLED PLACEMENT")
print("========================================")
print()


# ==================================================
# STEP 1 — SPLIT FILE
# ==================================================

split_file()


# ==================================================
# GET BLOCK LIST
# ==================================================

block_files = sorted(
    os.listdir(
        BLOCK_FOLDER
    )
)


print()
print(
    f"Total blocks: {len(block_files)}"
)


# ==================================================
# STEP 2 — PROCESS EACH BLOCK
# ==================================================

print()
print(
    "Requesting placement from Master..."
)
print()


successful_blocks = 0


for block_name in block_files:

    block_path = os.path.join(
        BLOCK_FOLDER,
        block_name
    )


    print()
    print("----------------------------------------")
    print(
        f"Processing: {block_name}"
    )
    print("----------------------------------------")


    # ----------------------------------------------
    # ASK MASTER
    # ----------------------------------------------

    placement = get_block_placement(
        block_name
    )


    if placement is None:

        print(
            "❌ Master request failed"
        )

        continue


    # ----------------------------------------------
    # CHECK MASTER RESPONSE
    # ----------------------------------------------

    if placement["status"] != "PLACEMENT":

        print(
            "❌ Master could not provide placement"
        )

        print(
            "Response:",
            placement
        )

        continue


    # ----------------------------------------------
    # GET SELECTED NODES
    # ----------------------------------------------

    selected_nodes = placement[
        "nodes"
    ]


    print()
    print(
        "Master selected:"
    )


    for node in selected_nodes:

        print(
            f"  → {node['node_id']}"
        )


    # ----------------------------------------------
    # SEND BLOCK TO SELECTED NODES
    # ----------------------------------------------

    successful_replicas = 0


    for node in selected_nodes:

        success = send_block(
            block_path,
            node
        )


        if success:

            successful_replicas += 1


    # ----------------------------------------------
    # CHECK REPLICATION
    # ----------------------------------------------

    print()


    if successful_replicas == len(
        selected_nodes
    ):

        print(
            f"✓ Replication successful "
            f"({successful_replicas}/"
            f"{len(selected_nodes)})"
        )

        successful_blocks += 1


    elif successful_replicas > 0:

        print(
            f"⚠ Partial replication "
            f"({successful_replicas}/"
            f"{len(selected_nodes)})"
        )


    else:

        print(
            "❌ Block upload failed"
        )


# ==================================================
# UPLOAD COMPLETE
# ==================================================

print()
print("========================================")
print("       DISTRIBUTED UPLOAD COMPLETED")
print("========================================")

print()

print(
    f"Successful blocks: "
    f"{successful_blocks}/"
    f"{len(block_files)}"
)

print()