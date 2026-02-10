"""
Vector store for document embeddings.
Supports ChromaDB (local) and Pinecone (cloud) with tenant isolation.
"""

from typing import List, Dict, Optional
import os
import shutil
import sqlite3
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self):
        self.store_type = os.getenv('VECTOR_STORE_TYPE', 'chroma').lower()
        
        if self.store_type == 'pinecone':
            self._init_pinecone()
        else:
            self._init_chromadb()

    def _init_chromadb(self):
        """Initialize ChromaDB (local vector store)."""
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError as e:
            logger.error('chromadb is required but not installed: %s', e)
            raise

        persist_dir = os.getenv('CHROMA_PERSIST_DIRECTORY', './data/chroma_db')
        collection_name = os.getenv('CHROMA_COLLECTION_NAME', 'website_docs')

        os.makedirs(persist_dir, exist_ok=True)

        # Initialize client
        client = None
        try:
            client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
        except Exception as e:
            logger.warning('PersistentClient failed, trying Client: %s', e)
            try:
                settings = Settings(persist_directory=persist_dir, anonymized_telemetry=False)
                client = chromadb.Client(settings)
            except Exception as e2:
                logger.exception('Failed to initialize chromadb client: %s', e2)
                raise

        # Ensure collection exists
        try:
            collection = client.get_or_create_collection(
                name=collection_name,
                metadata={'description': 'Website content embeddings'}
            )
            logger.info('Loaded ChromaDB collection: %s', collection_name)
        except Exception as e:
            # Handle sqlite schema incompatibilities
            if 'no such column' in str(e).lower() or isinstance(e, sqlite3.OperationalError):
                sqlite_file = os.path.join(persist_dir, 'chroma.sqlite3')
                if os.path.exists(sqlite_file):
                    backup = sqlite_file + '.bak'
                    shutil.move(sqlite_file, backup)
                    logger.warning('Backed up incompatible Chroma sqlite DB to %s', backup)
                collection = client.get_or_create_collection(
                    name=collection_name,
                    metadata={'description': 'Website content embeddings'}
                )
                logger.info('Created new ChromaDB collection after backup: %s', collection_name)
            else:
                logger.exception('Failed to create Chroma collection: %s', e)
                raise

        self.client = client
        self.collection = collection
        self.collection_name = collection_name
        self.store_type = 'chroma'

    def _refresh_collection(self):
        """Re-acquire the ChromaDB collection reference (used after reset)."""
        if self.store_type == 'chroma' and hasattr(self, 'client'):
            try:
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={'description': 'Website content embeddings'}
                )
                logger.info('Refreshed ChromaDB collection reference: %s', self.collection_name)
            except Exception as e:
                logger.error('Failed to refresh ChromaDB collection: %s', e)

    def _init_pinecone(self):
        """Initialize Pinecone (cloud vector store)."""
        try:
            from pinecone import Pinecone
        except ImportError as e:
            logger.error('pinecone-client is required but not installed: %s', e)
            raise

        api_key = os.getenv('PINECONE_API_KEY')
        if not api_key:
            raise ValueError('PINECONE_API_KEY environment variable is not set')

        self.pc = Pinecone(api_key=api_key)
        index_name = os.getenv('PINECONE_INDEX_NAME', 'website-docs')

        # Check if index exists
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]
        if index_name not in existing_indexes:
            # Create index
            environment = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
            self.pc.create_index(
                name=index_name,
                dimension=384,  # sentence-transformers all-MiniLM-L6-v2
                metric='cosine',
                spec={'serverless': {'cloud': 'aws', 'region': environment}}
            )
            logger.info('Created Pinecone index: %s', index_name)

        self.index = self.pc.Index(index_name)
        logger.info('Connected to Pinecone index: %s', index_name)

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        ids: List[str]
    ):
        """Add documents with embeddings to vector store."""
        if not documents:
            logger.warning('No documents to add')
            return

        # Filter out any None embeddings
        valid_items = [
            (doc, emb, meta, id_)
            for doc, emb, meta, id_ in zip(documents, embeddings, metadatas, ids)
            if emb is not None
        ]

        if not valid_items:
            logger.warning('No valid embeddings to add')
            return

        documents, embeddings, metadatas, ids = zip(*valid_items)

        if self.store_type == 'chroma':
            self._add_to_chromadb(list(documents), list(embeddings), list(metadatas), list(ids))
        elif self.store_type == 'pinecone':
            self._add_to_pinecone(list(documents), list(embeddings), list(metadatas), list(ids))

    def _add_to_chromadb(self, documents, embeddings, metadatas, ids):
        """Add documents to ChromaDB."""
        try:
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info('Added %d documents to ChromaDB', len(documents))
        except Exception as e:
            logger.exception('Error adding documents to ChromaDB: %s', e)
            raise

    def _add_to_pinecone(self, documents, embeddings, metadatas, ids):
        """Add documents to Pinecone."""
        try:
            vectors = []
            namespace = None
            for doc, emb, meta, id_ in zip(documents, embeddings, metadatas, ids):
                # Pinecone expects metadata as key-value pairs
                metadata = {k: v for k, v in meta.items() if isinstance(v, (str, int, float, bool))}
                metadata['text'] = doc  # Store the document text in metadata

                # Capture namespace for client isolation if present
                if not namespace and isinstance(meta, dict) and meta.get('client_id'):
                    namespace = str(meta.get('client_id'))

                vectors.append({
                    'id': id_,
                    'values': emb,
                    'metadata': metadata
                })

            # Use namespace (per-tenant) if provided for isolation
            if namespace:
                self.index.upsert(vectors=vectors, namespace=namespace)
            else:
                self.index.upsert(vectors=vectors)
            logger.info('Added %d documents to Pinecone', len(documents))
        except Exception as e:
            logger.exception('Error adding documents to Pinecone: %s', e)
            raise

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """Search for similar documents."""
        if self.store_type == 'chroma':
            return self._search_chromadb(query_embedding, top_k, where)
        elif self.store_type == 'pinecone':
            return self._search_pinecone(query_embedding, top_k, where)

    def _search_chromadb(self, query_embedding, top_k, where):
        """Search ChromaDB."""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where
            )
            return results
        except Exception as e:
            # Handle stale collection reference (e.g. after reset by another instance)
            if 'does not exist' in str(e).lower() or 'NotFoundError' in type(e).__name__:
                logger.warning('Collection reference is stale, refreshing...')
                self._refresh_collection()
                try:
                    results = self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=top_k,
                        where=where
                    )
                    return results
                except Exception as retry_e:
                    logger.exception('Error searching ChromaDB after refresh: %s', retry_e)
            else:
                logger.exception('Error searching ChromaDB: %s', e)
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

    def _search_pinecone(self, query_embedding, top_k, where):
        """Search Pinecone."""
        try:
            # Convert where clause to Pinecone filter format if needed
            filter_dict = None
            namespace = None
            if where:
                where_copy = dict(where)
                # If client_id is passed in where, use it as namespace
                if 'client_id' in where_copy:
                    namespace = where_copy.pop('client_id')
                filter_dict = where_copy if where_copy else None

            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter_dict,
                include_metadata=True,
                namespace=namespace
            )

            # Convert Pinecone results to ChromaDB-like format for compatibility
            documents = [[match.metadata.get('text', '') for match in results.matches]]
            metadatas = [[{k: v for k, v in match.metadata.items() if k != 'text'} for match in results.matches]]
            distances = [[match.score for match in results.matches]]

            return {
                'documents': documents,
                'metadatas': metadatas,
                'distances': distances
            }
        except Exception as e:
            logger.exception('Error searching Pinecone: %s', e)
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

    def count(self) -> int:
        """Get count of documents in collection/index."""
        if self.store_type == 'chroma':
            try:
                return int(self.collection.count())
            except Exception as e:
                # Handle stale collection reference
                if 'does not exist' in str(e).lower() or 'NotFoundError' in type(e).__name__:
                    self._refresh_collection()
                    try:
                        return int(self.collection.count())
                    except Exception:
                        return 0
                return 0
        elif self.store_type == 'pinecone':
            try:
                stats = self.index.describe_index_stats()
                return stats.total_vector_count
            except Exception as e:
                logger.exception('Error getting Pinecone count: %s', e)
                return 0

    def delete_collection(self):
        """Delete the collection/index."""
        if self.store_type == 'chroma':
            try:
                self.client.delete_collection(self.collection.name)
                logger.info('Deleted ChromaDB collection: %s', self.collection.name)
            except Exception as e:
                logger.exception('Error deleting ChromaDB collection: %s', e)
        elif self.store_type == 'pinecone':
            try:
                index_name = os.getenv('PINECONE_INDEX_NAME', 'website-docs')
                self.pc.delete_index(index_name)
                logger.info('Deleted Pinecone index: %s', index_name)
            except Exception as e:
                logger.exception('Error deleting Pinecone index: %s', e)

    def reset_collection(self):
        """Reset the collection/index (delete and recreate)."""
        if self.store_type == 'chroma':
            collection_name = self.collection.name
            self.delete_collection()
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={'description': 'Website content embeddings'}
            )
            logger.info('Reset ChromaDB collection: %s', collection_name)
        elif self.store_type == 'pinecone':
            index_name = os.getenv('PINECONE_INDEX_NAME', 'website-docs')
            environment = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
            self.delete_collection()
            # Recreate the index
            self.pc.create_index(
                name=index_name,
                dimension=384,
                metric='cosine',
                spec={'serverless': {'cloud': 'aws', 'region': environment}}
            )
            self.index = self.pc.Index(index_name)
            logger.info('Reset Pinecone index: %s', index_name)

    def delete_documents(self, where: Dict):
        """Delete documents from vector store based on metadata filter."""
        if not where:
            logger.warning("No filter provided for deletion")
            return

        try:
            if self.store_type == 'chroma':
                self.collection.delete(where=where)
                logger.info("Deleted documents from ChromaDB matching: %s", where)
            elif self.store_type == 'pinecone':
                # Try delete by metadata (works on serverless indexes)
                try:
                    self.index.delete(filter=where)
                    logger.info("Deleted documents from Pinecone matching: %s", where)
                except Exception as e:
                    logger.warning("Pinecone metadata deletion failed: %s", e)
        except Exception as e:
            logger.error("Error deleting documents: %s", e)
            raise


# Usage example
if __name__ == '__main__':
    store = VectorStore()
    print(f'Store type: {store.store_type}')
    print(f'Current document count: {store.count()}')
