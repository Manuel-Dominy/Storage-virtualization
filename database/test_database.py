import sqlite3
import os


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
# CONNECT TO DATABASE
# ==================================================

connection = sqlite3.connect(
    DATABASE_PATH
)

cursor = connection.cursor()


# ==================================================
# CREATE NODES TABLE
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS nodes (

    node_id TEXT PRIMARY KEY,

    host TEXT NOT NULL,

    port INTEGER NOT NULL,

    status TEXT NOT NULL,

    last_seen REAL

)
""")


# ==================================================
# CREATE BLOCKS TABLE
# ==================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS blocks (

    block_name TEXT NOT NULL,

    node_id TEXT NOT NULL,

    PRIMARY KEY (block_name, node_id),

    FOREIGN KEY (node_id)
        REFERENCES nodes(node_id)

)
""")


# ==================================================
# SAVE CHANGES
# ==================================================

connection.commit()


# ==================================================
# CLOSE DATABASE
# ==================================================

connection.close()


print("========================================")
print("DATABASE CREATED SUCCESSFULLY")
print("========================================")

print()
print("Database:")
print(DATABASE_PATH)

print()
print("Tables created:")
print("1. nodes")
print("2. blocks")