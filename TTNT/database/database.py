import os
import sqlite3
from sqlite3 import Connection


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.connection = None
        return cls._instance

    def connect(self) -> Connection:
        if self.connection is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "attendance.db")

            self.connection = sqlite3.connect(
                db_path,
                check_same_thread=False
            )

            self.connection.row_factory = sqlite3.Row

        return self.connection

    def cursor(self):
        return self.connect().cursor()

    def commit(self):
        self.connect().commit()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None