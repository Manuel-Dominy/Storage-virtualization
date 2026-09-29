import sqlite3


DATABASE_PATH = r"D:\DistributedFileSystem\database\dfs.db"


connection = sqlite3.connect(
    DATABASE_PATH
)

cursor = connection.cursor()


# ==================================================
# SHOW NODES
# ==================================================

print()
print("========================================")
print("NODES TABLE")
print("========================================")


cursor.execute("""
SELECT
    node_id,
    host,
    port,
    status,
    last_seen
FROM nodes
""")


rows = cursor.fetchall()


for row in rows:

    print(row)


# ==================================================
# SHOW BLOCKS
# ==================================================

print()
print("========================================")
print("BLOCKS TABLE")
print("========================================")


cursor.execute("""
SELECT
    block_name,
    node_id
FROM blocks
""")


rows = cursor.fetchall()


for row in rows:

    print(row)


connection.close()