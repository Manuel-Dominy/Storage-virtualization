import socket
import os

HOST = "127.0.0.1"
PORT = 5003

STORAGE_FOLDER = r"D:\DistributedFileSystem\storage\node3"

os.makedirs(STORAGE_FOLDER, exist_ok=True)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((HOST, PORT))
server.listen(5)

print("Node 1 is running...")
print(f"Listening on {HOST}:{PORT}")

while True:

    connection, address = server.accept()

    print(f"Connected by {address}")

    file_name = connection.recv(1024).decode()

    print("Receiving:", file_name)

    connection.send("READY".encode())

    file_path = os.path.join(STORAGE_FOLDER, file_name)

    with open(file_path, "wb") as file:

        while True:

            data = connection.recv(4096)

            if not data:
                break

            file.write(data)

    print("File stored successfully!")
    print("Location:", file_path)

    connection.close()