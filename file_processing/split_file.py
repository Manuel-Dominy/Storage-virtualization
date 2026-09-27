import os

FILE_PATH = r"D:\DistributedFileSystem\test_files\sample.txt"

BLOCK_SIZE = 20

OUTPUT_FOLDER = r"D:\DistributedFileSystem\file_processing\blocks"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

with open(FILE_PATH, "rb") as file:

    block_number = 1

    while True:

        data = file.read(BLOCK_SIZE)

        if not data:
            break

        block_name = f"block_{block_number:03d}.dat"

        block_path = os.path.join(
            OUTPUT_FOLDER,
            block_name
        )

        with open(block_path, "wb") as block_file:
            block_file.write(data)

        print(f"Created: {block_name}")

        block_number += 1

print("File splitting completed.")