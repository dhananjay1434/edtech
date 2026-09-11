from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from pymongo.client_session import ClientSession
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from pymongo.read_preferences import ReadPreference
from contextlib import contextmanager
from typing import Iterator, Generator, Callable, TypeVar, Any
from .config import settings

T = TypeVar('T')

class DatabaseAdapter:
    def __init__(self, uri: str, db_name: str):
        self.client: MongoClient = MongoClient(uri, retryWrites=False)
        self.db_name = db_name
        self.db = self.client[db_name]
        self._is_replica_set = None

    def check_replica_set(self) -> bool:
        if self._is_replica_set is None:
            try:
                self.client.admin.command("replSetGetStatus")
                self._is_replica_set = True
            except OperationFailure:
                self._is_replica_set = False
        return self._is_replica_set

    def get_session(self) -> ClientSession:
        return self.client.start_session()

    @contextmanager
    def unit_of_work(self) -> Generator[ClientSession, None, None]:
        if not self.check_replica_set():
            raise RuntimeError(
                "MongoDB is not running as a replica set, so transactions are "
                "unavailable. Refusing to process. Start MongoDB with --replSet."
            )
        with self.get_session() as session:
            session.start_transaction(
                read_concern=ReadConcern("snapshot"),
                write_concern=WriteConcern(w="majority"),
                read_preference=ReadPreference.PRIMARY,
            )
            try:
                yield session
                session.commit_transaction()
            except Exception:
                session.abort_transaction()
                raise
db_adapter = DatabaseAdapter(settings.mongodb_uri, settings.mongodb_db_name)

def get_db():
    return db_adapter.db

def get_db_adapter():
    return db_adapter
