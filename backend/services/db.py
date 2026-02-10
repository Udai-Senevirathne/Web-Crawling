"""
Database utility - supports MongoDB or in-memory storage for simplicity.

Set USE_FAKE_DB=1 in .env to use in-memory storage (good for quick testing).
Set USE_FAKE_DB=0 or remove it to use real MongoDB.
"""
from dotenv import load_dotenv
import os
import logging

load_dotenv()

_client = None
_fake_db = None
logger = logging.getLogger(__name__)


class FakeCollection:
    """Simple in-memory collection for development without MongoDB."""
    
    def __init__(self, name):
        self.name = name
        self._data = {}
    
    def find_one(self, query):
        for doc in self._data.values():
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None
    
    def find(self, query=None):
        if query is None:
            return FakeCursor(list(self._data.values()))
        results = []
        for doc in self._data.values():
            if all(doc.get(k) == v for k, v in query.items()):
                results.append(doc)
        return FakeCursor(results)
    
    def insert_one(self, doc):
        doc_id = doc.get('_id') or str(len(self._data) + 1)
        doc['_id'] = doc_id
        self._data[doc_id] = doc
        return type('InsertResult', (), {'inserted_id': doc_id})()
    
    def update_one(self, query, update, upsert=False):
        for doc_id, doc in self._data.items():
            if all(doc.get(k) == v for k, v in query.items()):
                if '$set' in update:
                    doc.update(update['$set'])
                if '$inc' in update:
                    for k, v in update['$inc'].items():
                        doc[k] = doc.get(k, 0) + v
                return type('UpdateResult', (), {'matched_count': 1, 'modified_count': 1})()
        # No match found — upsert if requested
        if upsert:
            new_doc = dict(query)
            if '$set' in update:
                new_doc.update(update['$set'])
            if '$inc' in update:
                for k, v in update['$inc'].items():
                    new_doc[k] = v
            self.insert_one(new_doc)
            return type('UpdateResult', (), {'matched_count': 0, 'modified_count': 0, 'upserted_id': new_doc.get('_id')})()
        return type('UpdateResult', (), {'matched_count': 0, 'modified_count': 0})()
    
    def delete_one(self, query):
        for doc_id, doc in list(self._data.items()):
            if all(doc.get(k) == v for k, v in query.items()):
                del self._data[doc_id]
                return type('DeleteResult', (), {'deleted_count': 1})()
        return type('DeleteResult', (), {'deleted_count': 0})()
    
    def count_documents(self, query=None):
        if query is None:
            return len(self._data)
        return len(self.find(query)._results)

    def delete_many(self, query):
        if not query:
            count = len(self._data)
            self._data.clear()
            return type('DeleteResult', (), {'deleted_count': count})()
        to_delete = []
        for doc_id, doc in self._data.items():
            if all(doc.get(k) == v for k, v in query.items()):
                to_delete.append(doc_id)
        for doc_id in to_delete:
            del self._data[doc_id]
        return type('DeleteResult', (), {'deleted_count': len(to_delete)})()


class FakeCursor:
    """Fake cursor for in-memory queries."""
    
    def __init__(self, results):
        self._results = results
    
    def sort(self, key, direction=1):
        try:
            self._results.sort(
                key=lambda x: x.get(key, '') if not isinstance(key, str) or x.get(key) is not None else '',
                reverse=(direction == -1)
            )
        except TypeError:
            pass  # Gracefully handle uncomparable values
        return self
    
    def limit(self, n):
        self._results = self._results[:n]
        return self
    
    def __iter__(self):
        return iter(self._results)
    
    def __list__(self):
        return self._results


class FakeDB:
    """Fake database for development without MongoDB."""
    
    def __init__(self):
        self._collections = {}
    
    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        if name not in self._collections:
            self._collections[name] = FakeCollection(name)
        return self._collections[name]


def use_fake_db() -> bool:
    """Check if we should use fake/in-memory DB."""
    return os.getenv('USE_FAKE_DB', '0') == '1'


def get_mongo_client():
    """Return a MongoClient. Falls back to fake if MongoDB unavailable."""
    global _client
    
    if use_fake_db():
        logger.info('Using in-memory fake database (USE_FAKE_DB=1)')
        return None
    
    if _client is None:
        try:
            from pymongo import MongoClient
            mongo_uri = os.getenv('DATABASE_URL')
            if not mongo_uri:
                logger.warning('DATABASE_URL not set, falling back to fake DB')
                return None
            
            _client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Force a server selection to surface auth/connect errors early
            _client.server_info()
            logger.info('Connected to MongoDB')
        except Exception as e:
            logger.warning('Could not connect to MongoDB: %s. Using fake DB.', e)
            return None
    
    return _client


def get_db():
    """Get database instance - real MongoDB or fake in-memory."""
    global _fake_db
    
    client = get_mongo_client()
    
    if client is None:
        # Use fake database
        if _fake_db is None:
            _fake_db = FakeDB()
            logger.info('Initialized in-memory database')
        return _fake_db
    
    db_name = os.getenv('MONGODB_DATABASE', 'web_crawler')
    return client[db_name]
