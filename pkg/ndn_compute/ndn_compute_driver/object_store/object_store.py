import os
import sqlite3
import subprocess
import re
from uuid import UUID


class DriverObjectStore:
    """
    Represents an object store used by the Driver (one object store per Driver).
    """
    def __init__(self, database: str, collections: list[str], create_collections: bool = False):
        """
        :param database: Path to a sqlite database (will be created if not exists)
        :param collections: Names of collections (tables) in the database (e.g., 'Transformation')
        :param create_collections: Whether to run SQL to create the collections if they do not exist.
        """
        self.database_path = database
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
        """
        Run SQL to create the collections if they do not exist.
        """
        for collection in self.collections:
            cursor = self.conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS "{}" (
                    Id TEXT PRIMARY KEY,
                    Value BLOB
                )
                '''.format(collection))

            self.conn.commit()

    def create_object(self, collection: str, object_id: UUID, value: bytes) -> None:
        """
        Save an object in the specified collection (as a new row in a table)

        :param collection: The collection (table) to save the object in
        :param object_id: The object ID (primary key value) for the new row, always a UUID
        :param value: The bytes to save in the new row
        :raises Exception: Cannot find the collection
        """
        if collection not in self.collections:
            raise Exception("Cannot insert into unregistered collection")

        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO "{}" (Id, Value) 
        VALUES (?, ?)
        '''.format(collection), (str(object_id), sqlite3.Binary(value)))

        self.conn.commit()

    def retrieve_object(self, collection: str, object_id: UUID) -> bytes:
        """
        Fetch an object from the specified collection

        :param collection: The collection (table) to retrieve the object from
        :param object_id: The object ID (primary key value) of the object
        :return: The bytes saved as the value in the row
        :raises Exception: Cannot find the collection or an object with the specified object ID
        """
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
        """
        Serve the object store as an NDN App accepting interests for objects, detached as a new process.

        The server should still see any later-committed objects in the sqlite database.
        """
        subprocess.Popen([
                "python", "-m",
                "ndn_compute_driver.object_store.server",
                "--database", self.database_path,
                "--collections", *self.collections
             ],
            preexec_fn=os.setsid  # Detach the process
        )

    def shutdown(self):
        """
        Terminate the handle to the object store.

        Note that any detached object server will still be running. (fix this?)
        """
        self.conn.close()

