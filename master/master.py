import socket
import json
import threading
import time
import sqlite3
import os


# ==================================================
# MASTER CONFIGURATION
# ==================================================

HOST = "127.0.0.1"
PORT = 6000

HEARTBEAT_TIMEOUT = 10

# Each block must have 2 replicas
REPLICATION_FACTOR = 2


# ==================================================
# DATABASE CONFIGURATION
# ==================================================

DATABASE_FOLDER = r"D:\DistributedFileSystem\database"

DATABASE_PATH = os.path.join(
    DATABASE_FOLDER,
    "dfs.db"
)


# Make sure database folder exists
os.makedirs(
    DATABASE_FOLDER,
    exist_ok=True
)


# ==================================================
# MASTER MEMORY
# ==================================================

# Stores currently known nodes in memory

nodes = {}


# Used to rotate block placement

placement_counter = 0


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_database_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    return connection


# ==================================================
# INITIALIZE DATABASE
# ==================================================

def initialize_database():

    connection = get_database_connection()

    cursor = connection.cursor()


    # ------------------------------------------------
    # NODES TABLE
    # ------------------------------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nodes (

        node_id TEXT PRIMARY KEY,

        host TEXT NOT NULL,

        port INTEGER NOT NULL,

        status TEXT NOT NULL,

        last_seen REAL

    )
    """)


    # ------------------------------------------------
    # BLOCKS TABLE
    # ------------------------------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blocks (

        block_name TEXT NOT NULL,

        node_id TEXT NOT NULL,

        PRIMARY KEY (block_name, node_id),

        FOREIGN KEY (node_id)
            REFERENCES nodes(node_id)

    )
    """)


    connection.commit()

    connection.close()


# ==================================================
# SAVE NODE TO DATABASE
# ==================================================

def save_node_to_database(
    node_id,
    host,
    port,
    status,
    last_seen
):

    connection = get_database_connection()

    cursor = connection.cursor()


    cursor.execute("""
    INSERT OR REPLACE INTO nodes
    (
        node_id,
        host,
        port,
        status,
        last_seen
    )
    VALUES (?, ?, ?, ?, ?)
    """,
    (
        node_id,
        host,
        port,
        status,
        last_seen
    ))


    connection.commit()

    connection.close()


# ==================================================
# UPDATE NODE STATUS
# ==================================================

def update_node_status(
    node_id,
    status,
    last_seen
):

    connection = get_database_connection()

    cursor = connection.cursor()


    cursor.execute("""
    UPDATE nodes

    SET
        status = ?,
        last_seen = ?

    WHERE node_id = ?
    """,
    (
        status,
        last_seen,
        node_id
    ))


    connection.commit()

    connection.close()


# ==================================================
# CHOOSE NODES FOR A BLOCK
# ==================================================

def choose_nodes_for_block():

    global placement_counter


    # ----------------------------------------------
    # FIND ONLINE NODES
    # ----------------------------------------------

    online_nodes = []


    for node_id in nodes:

        if nodes[node_id]["status"] == "ONLINE":

            online_nodes.append(
                node_id
            )


    # ----------------------------------------------
    # CHECK REPLICATION POSSIBILITY
    # ----------------------------------------------

    if len(online_nodes) < REPLICATION_FACTOR:

        return []


    # ----------------------------------------------
    # STARTING POSITION
    # ----------------------------------------------

    start_index = (
        placement_counter
        % len(online_nodes)
    )


    # ----------------------------------------------
    # SELECT REPLICAS
    # ----------------------------------------------

    selected_nodes = []


    for i in range(REPLICATION_FACTOR):

        index = (
            start_index + i
        ) % len(online_nodes)


        selected_nodes.append(
            online_nodes[index]
        )


    # Move placement position
    placement_counter += 1


    return selected_nodes


# ==================================================
# SAVE BLOCK LOCATION
# ==================================================

def save_block_locations(
    block_name,
    selected_nodes
):

    connection = get_database_connection()

    cursor = connection.cursor()


    for node_id in selected_nodes:

        cursor.execute("""
        INSERT OR IGNORE INTO blocks
        (
            block_name,
            node_id
        )
        VALUES (?, ?)
        """,
        (
            block_name,
            node_id
        ))


    connection.commit()

    connection.close()


# ==================================================
# HANDLE NODE FAILURE
# ==================================================

def check_nodes():

    while True:

        # Check every 5 seconds
        time.sleep(5)


        current_time = time.time()


        # Check every registered node
        for node_id in nodes:

            last_seen = (
                nodes[node_id]["last_seen"]
            )


            time_since_heartbeat = (
                current_time - last_seen
            )


            # ======================================
            # NODE FAILED
            # ======================================

            if (
                time_since_heartbeat
                > HEARTBEAT_TIMEOUT
            ):

                if (
                    nodes[node_id]["status"]
                    != "FAILED"
                ):

                    nodes[node_id]["status"] = (
                        "FAILED"
                    )


                    update_node_status(
                        node_id,
                        "FAILED",
                        last_seen
                    )


                    print()
                    print(
                        f"❌ {node_id} FAILED"
                    )


                    print(
                        "   No heartbeat received "
                        f"for {int(time_since_heartbeat)} "
                        "seconds."
                    )


            # ======================================
            # NODE RECOVERED
            # ======================================

            else:

                if (
                    nodes[node_id]["status"]
                    == "FAILED"
                ):

                    nodes[node_id]["status"] = (
                        "ONLINE"
                    )


                    update_node_status(
                        node_id,
                        "ONLINE",
                        last_seen
                    )


                    print()
                    print(
                        f"✓ {node_id} is ONLINE again"
                    )


# ==================================================
# HANDLE CLIENT/NODE CONNECTION
# ==================================================

def handle_connection(connection):

    try:

        # ------------------------------------------
        # RECEIVE DATA
        # ------------------------------------------

        data = connection.recv(
            4096
        ).decode()


        if not data:

            return


        # ------------------------------------------
        # CONVERT JSON → PYTHON DICTIONARY
        # ------------------------------------------

        message = json.loads(
            data
        )


        message_type = message["type"]


        # ==================================================
        # NODE REGISTRATION
        # ==================================================

        if message_type == "REGISTER_NODE":

            node_id = message["node_id"]

            node_host = message["host"]

            node_port = message["port"]


            current_time = time.time()


            # ------------------------------------------
            # STORE IN MASTER MEMORY
            # ------------------------------------------

            nodes[node_id] = {

                "host":
                    node_host,

                "port":
                    node_port,

                "status":
                    "ONLINE",

                "last_seen":
                    current_time

            }


            # ------------------------------------------
            # STORE IN SQLITE
            # ------------------------------------------

            save_node_to_database(
                node_id,
                node_host,
                node_port,
                "ONLINE",
                current_time
            )


            print()
            print(
                f"✓ Registered: {node_id}"
            )

            print(
                f"  Host: {node_host}"
            )

            print(
                f"  Port: {node_port}"
            )


            response = {

                "status":
                    "REGISTERED",

                "message":
                    f"{node_id} registered successfully"

            }


        # ==================================================
        # HEARTBEAT
        # ==================================================

        elif message_type == "HEARTBEAT":

            node_id = message["node_id"]


            # ------------------------------------------
            # CHECK NODE
            # ------------------------------------------

            if node_id in nodes:

                current_time = time.time()


                # --------------------------------------
                # UPDATE MEMORY
                # --------------------------------------

                nodes[node_id]["last_seen"] = (
                    current_time
                )

                nodes[node_id]["status"] = (
                    "ONLINE"
                )


                # --------------------------------------
                # UPDATE DATABASE
                # --------------------------------------

                update_node_status(
                    node_id,
                    "ONLINE",
                    current_time
                )


                print(
                    f"♥ Heartbeat from {node_id}"
                )


                response = {

                    "status":
                        "HEARTBEAT_RECEIVED"

                }


            else:

                print(
                    f"⚠ Unknown node: {node_id}"
                )


                response = {

                    "status":
                        "NODE_NOT_REGISTERED"

                }


        # ==================================================
        # BLOCK PLACEMENT REQUEST
        # ==================================================

        elif message_type == "GET_BLOCK_PLACEMENT":

            block_name = message["block_name"]


            print()
            print(
                "Placement request received"
            )

            print(
                f"Block: {block_name}"
            )


            # ------------------------------------------
            # CHOOSE NODES
            # ------------------------------------------

            selected_nodes = (
                choose_nodes_for_block()
            )


            # ------------------------------------------
            # NOT ENOUGH NODES
            # ------------------------------------------

            if (
                len(selected_nodes)
                < REPLICATION_FACTOR
            ):

                print(
                    "❌ Not enough online nodes "
                    "for replication."
                )


                response = {

                    "status":
                        "INSUFFICIENT_NODES",

                    "message":
                        "Not enough online nodes "
                        "for requested replication factor",

                    "required":
                        REPLICATION_FACTOR,

                    "available":
                        len(selected_nodes)

                }


            # ------------------------------------------
            # PLACEMENT SUCCESSFUL
            # ------------------------------------------

            else:

                node_information = []


                for node_id in selected_nodes:

                    node_information.append({

                        "node_id":
                            node_id,

                        "host":
                            nodes[node_id]["host"],

                        "port":
                            nodes[node_id]["port"]

                    })


                # --------------------------------------
                # SAVE BLOCK METADATA
                # --------------------------------------

                save_block_locations(
                    block_name,
                    selected_nodes
                )


                # --------------------------------------
                # DISPLAY PLACEMENT
                # --------------------------------------

                print(
                    "Replicas selected:"
                )


                for node_id in selected_nodes:

                    print(
                        f"  → {node_id}"
                    )


                print(
                    f"Replication: "
                    f"{len(selected_nodes)}/"
                    f"{REPLICATION_FACTOR}"
                )


                # --------------------------------------
                # SEND RESPONSE TO CLIENT
                # --------------------------------------

                response = {

                    "status":
                        "PLACEMENT",

                    "block_name":
                        block_name,

                    "nodes":
                        node_information

                }


        # ==================================================
        # UNKNOWN REQUEST
        # ==================================================

        else:

            print()
            print(
                f"⚠ Unknown message type: "
                f"{message_type}"
            )


            response = {

                "status":
                    "UNKNOWN_REQUEST"

            }


        # ==================================================
        # SEND RESPONSE
        # ==================================================

        connection.send(
            json.dumps(
                response
            ).encode()
        )


    # ==================================================
    # ERROR HANDLING
    # ==================================================

    except json.JSONDecodeError:

        print(
            "❌ Invalid JSON received"
        )


    except Exception as error:

        print(
            "❌ Connection error:",
            error
        )


    finally:

        connection.close()


# ==================================================
# INITIALIZE DATABASE
# ==================================================

initialize_database()


# ==================================================
# CREATE MASTER SOCKET
# ==================================================

server = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)


# Allow quick server restart

server.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1
)


# ==================================================
# BIND MASTER
# ==================================================

server.bind(
    (
        HOST,
        PORT
    )
)


# ==================================================
# LISTEN
# ==================================================

server.listen(10)


# ==================================================
# MASTER STARTUP MESSAGE
# ==================================================

print()
print("========================================")
print("       DISTRIBUTED FILE SYSTEM")
print("            MASTER SERVER")
print("========================================")

print()

print(
    f"Master listening on {HOST}:{PORT}"
)

print(
    f"Heartbeat timeout: "
    f"{HEARTBEAT_TIMEOUT} seconds"
)

print(
    f"Replication factor: "
    f"{REPLICATION_FACTOR}"
)

print(
    f"Database: "
    f"{DATABASE_PATH}"
)

print()

print(
    "Waiting for nodes and clients..."
)

print()


# ==================================================
# START FAILURE MONITOR
# ==================================================

monitor_thread = threading.Thread(
    target=check_nodes,
    daemon=True
)

monitor_thread.start()


# ==================================================
# ACCEPT CONNECTIONS
# ==================================================

while True:

    connection, address = server.accept()


    print()
    print(
        "Connection received from:",
        address
    )


    # Handle connection in separate thread

    thread = threading.Thread(
        target=handle_connection,
        args=(connection,)
    )


    thread.start()