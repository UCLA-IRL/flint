import os
import uuid
import sqlite3
import subprocess
import re


class NdnDriverObjectStore:
    def __init__(self, database: str, collections: list[str], create_collections: bool = False):
        self.conn = sqlite3.connect(database)
        self.collections = collections

        for collection in collections:
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", collection):
                raise ValueError(f"Invalid table name: {collection}")

        if create_collections:
            self.ensure_collections_exist()

    def __del__(self):
        self.shutdown()

    def ensure_collections_exist(self) -> None:
        for collection in self.collections:
            cursor = self.conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS "{}" (
                    Id TEXT PRIMARY KEY,
                    Value BLOB
                )
                '''.format(collection))

            self.conn.commit()

    def create_object(self, collection: str, object_id: uuid, value: bytes) -> None:
        if collection not in self.collections:
            raise Exception("Cannot insert into unregistered collection")

        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO "{}" (Id, Value) 
        VALUES (?, ?)
        '''.format(collection), (str(object_id), value))

        self.conn.commit()

    def retrieve_object(self, collection: str, object_id: uuid) -> bytes:
        if collection not in self.collections:
            raise Exception("Cannot read from unregistered collection")

        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM "{}" WHERE Id = ?'.format(collection),
                       (str(object_id), ))
        row = cursor.fetchone()

        if row:
            return row[1]

        raise Exception("Object with specified Id not found")

    def serve_detached(self):
        subprocess.Popen(
            ["python", "-m", "ndn_driver_object_store.ndn_driver_object_server"],
            preexec_fn=os.setsid  # Detach the process
        )

    def shutdown(self):
        self.conn.close()

