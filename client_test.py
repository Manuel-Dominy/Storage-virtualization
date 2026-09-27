import socket
import os

HOST = "127.0.0.1"
PORT = 5001

FILE_PATH = r"D:\DistributedFileSystem\test_files\sample.txt"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((HOST, PORT))

print("Connected to Node 1")

file_name = os.path.basename(FILE_PATH)

client.send(file_name.encode())

response = client.recv(1024).decode()

if response == "READY":

    print("Node 1 is ready")

    with open(FILE_PATH, "rb") as file:

        while True:

            data = file.read(4096)

            if not data:
                break

            client.send(data)

    print("File sent successfully")

client.close()