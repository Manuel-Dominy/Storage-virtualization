import socket
import os


# --------------------------------------------------
# FILE CONFIGURATION
# --------------------------------------------------

FILE_PATH = r"D:\DistributedFileSystem\test_files\sample.txt"

BLOCK_FOLDER = r"D:\DistributedFileSystem\file_processing\blocks"

BLOCK_SIZE = 20


# --------------------------------------------------
# NODE CONFIGURATION
# --------------------------------------------------

NODES = [
    ("Node 1", "127.0.0.1", 5001),
    ("Node 2", "127.0.0.1", 5002),
    ("Node 3", "127.0.0.1", 5003)
]


# Each block will have 2 copies
REPLICATION_FACTOR = 2


# --------------------------------------------------
# SPLIT FILE INTO BLOCKS
# --------------------------------------------------

def split_file():

    os.makedirs(BLOCK_FOLDER, exist_ok=True)

    # Remove old blocks
    for file_name in os.listdir(BLOCK_FOLDER):

        file_path = os.path.join(
            BLOCK_FOLDER,
            file_name
        )

        if os.path.isfile(file_path):

            os.remove(file_path)

    print("Splitting file...")

    with open(FILE_PATH, "rb") as file:

        block_number = 1

        while True:

            data = file.read(BLOCK_SIZE)

            if not data:
                break

            block_name = f"block_{block_number:03d}.dat"

            block_path = os.path.join(
                BLOCK_FOLDER,
                block_name
            )

            with open(block_path, "wb") as block_file:

                block_file.write(data)

            print(f"Created: {block_name}")

            block_number += 1


# --------------------------------------------------
# SEND ONE BLOCK TO ONE NODE
# --------------------------------------------------

def send_block(
    block_path,
    node_name,
    node_host,
    node_port
):

    block_name = os.path.basename(block_path)

    try:

        client = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        client.settimeout(5)

        client.connect(
            (node_host, node_port)
        )

        # Send block filename
        client.send(block_name.encode())

        # Wait for node confirmation
        response = client.recv(1024).decode()

        if response != "READY":

            client.close()

            return False

        # Send block data
        with open(block_path, "rb") as file:

            while True:

                data = file.read(4096)

                if not data:
                    break

                client.send(data)

        client.close()

        print(
            f"  ✓ {block_name} → {node_name}"
        )

        return True

    except Exception as error:

        print(
            f"  ✗ {block_name} → {node_name} FAILED"
        )

        print(
            f"    Reason: {error}"
        )

        return False


# --------------------------------------------------
# MAIN DISTRIBUTED UPLOAD
# --------------------------------------------------

print()
print("========================================")
print(" DISTRIBUTED FILE UPLOAD")
print(" REPLICATION FACTOR = 2")
print("========================================")
print()


# Step 1
split_file()


# Get all generated blocks
block_files = sorted(
    os.listdir(BLOCK_FOLDER)
)


print()
print("Distributing and replicating blocks...")
print()


# --------------------------------------------------
# DISTRIBUTE BLOCKS
# --------------------------------------------------

for index, block_name in enumerate(block_files):

    block_path = os.path.join(
        BLOCK_FOLDER,
        block_name
    )

    print(block_name)

    successful_replicas = 0


    # Select two different nodes
    for replica in range(REPLICATION_FACTOR):

        node_index = (
            index + replica
        ) % len(NODES)


        node_name, node_host, node_port = NODES[
            node_index
        ]


        success = send_block(
            block_path,
            node_name,
            node_host,
            node_port
        )


        if success:

            successful_replicas += 1


    # ----------------------------------------------
    # CHECK REPLICATION
    # ----------------------------------------------

    if successful_replicas == REPLICATION_FACTOR:

        print(
            f"  ✓ Replication successful "
            f"({successful_replicas}/"
            f"{REPLICATION_FACTOR})"
        )

    elif successful_replicas >= 1:

        print(
            f"  ⚠ Only "
            f"{successful_replicas}/"
            f"{REPLICATION_FACTOR} replicas created"
        )

    else:

        print(
            "  ✗ No replica created"
        )


print()
print("========================================")
print(" DISTRIBUTED UPLOAD COMPLETED")
print("========================================")