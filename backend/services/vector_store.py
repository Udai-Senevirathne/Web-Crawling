"""
Vector store for document embeddings using ChromaDB.
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import os


class VectorStore:
    def __init__(self):
        persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma")

        # Create directory if it doesn't exist
        os.makedirs(persist_dir, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )

        collection_name = os.getenv("CHROMA_COLLECTION_NAME", "website_docs")

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"[OK] Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Website content embeddings"}
            )
            print(f"[OK] Created new collection: {collection_name}")

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        ids: List[str]
    ):
        """Add documents with embeddings to vector store."""
        if not documents:
            print("Warning: No documents to add")
            return

        # Filter out any None embeddings
        valid_items = [
            (doc, emb, meta, id_)
            for doc, emb, meta, id_ in zip(documents, embeddings, metadatas, ids)
            if emb is not None
        ]

        if not valid_items:
            print("Warning: No valid embeddings to add")
            return

        documents, embeddings, metadatas, ids = zip(*valid_items)

        try:
            self.collection.add(
                documents=list(documents),
                embeddings=list(embeddings),
                metadatas=list(metadatas),
                ids=list(ids)
            )
            print(f"[OK] Added {len(documents)} documents to vector store")
        except Exception as e:
            print(f"Error adding documents: {e}")
            raise

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """Search for similar documents."""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where
            )
            return results
        except Exception as e:
            print(f"Error searching vector store: {e}")
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

    def count(self) -> int:
        """Get count of documents in collection."""
        try:
            return self.collection.count()
        except Exception:
            return 0

    def delete_collection(self):
        """Delete the collection."""
        try:
            self.client.delete_collection(self.collection.name)
            print(f"[OK] Deleted collection: {self.collection.name}")
        except Exception as e:
            print(f"Error deleting collection: {e}")

    def reset_collection(self):
        """Reset the collection (delete and recreate)."""
        collection_name = self.collection.name
        self.delete_collection()
        self.collection = self.client.create_collection(
            name=collection_name,
            metadata={"description": "Website content embeddings"}
        )
        print(f"[OK] Reset collection: {collection_name}")


# Usage example
if __name__ == "__main__":
    store = VectorStore()

    print(f"Current document count: {store.count()}")

    # Test adding documents
    test_docs = ["Test document 1", "Test document 2"]
    test_embeddings = [[0.1] * 1536, [0.2] * 1536]  # Dummy embeddings
    test_metadatas = [{"source": "test1"}, {"source": "test2"}]
    test_ids = ["test_1", "test_2"]

    # store.add_documents(test_docs, test_embeddings, test_metadatas, test_ids)
    # print(f"Document count after adding: {store.count()}")

