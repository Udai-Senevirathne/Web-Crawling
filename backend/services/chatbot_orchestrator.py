"""
Main chatbot orchestration logic (RAG pipeline).
"""
from .embeddings import EmbeddingService
from .vector_store import VectorStore
from .llm_service import LLMService
from typing import Dict, List, Optional
import os


class ChatbotOrchestrator:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.llm_service = LLMService()
        self.top_k = int(os.getenv("TOP_K", "5"))
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))

    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """Process user query and generate response using RAG pipeline."""

        # Step 1: Generate query embedding
        print(f"Processing query: {query[:50]}...")
        query_embedding = self.embedding_service.generate_embedding(query)

        # Step 2: Search vector store for relevant documents
        search_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=self.top_k
        )

        # Step 3: Prepare context from retrieved documents
        context = self._prepare_context(search_results)
        sources = self._extract_sources(search_results)

        # Check if we have relevant context
        if not context or context.strip() == "":
            context = "No relevant information found in the knowledge base."

        # Step 4: Generate response using LLM
        response = self.llm_service.generate_response(
            query=query,
            context=context,
            conversation_history=conversation_history
        )

        # Step 5: Return structured response
        return {
            "response": response,
            "sources": sources,
            "session_id": session_id,
            "context_used": bool(sources)
        }

    def _prepare_context(self, search_results: Dict) -> str:
        """Format retrieved documents as context."""
        if not search_results or not search_results.get('documents'):
            return ""

        documents = search_results['documents'][0] if search_results['documents'] else []
        distances = search_results.get('distances', [[]])[0] if search_results.get('distances') else []

        context_parts = []

        for i, doc in enumerate(documents):
            # Skip if document is empty or similarity is too low
            if not doc or not doc.strip():
                continue

            # Check distance threshold if available (lower distance = higher similarity)
            if distances and i < len(distances):
                # ChromaDB uses L2 distance - convert to similarity
                # Typically want distance < 1.0 for good matches
                if distances[i] > 2.0:  # Adjust threshold as needed
                    continue

            context_parts.append(f"[Source {i+1}]\n{doc}\n")

        if not context_parts:
            return ""

        return "\n".join(context_parts[:self.top_k])

    def _extract_sources(self, search_results: Dict) -> List[Dict]:
        """Extract source information from search results."""
        if not search_results or not search_results.get('metadatas'):
            return []

        metadatas = search_results['metadatas'][0] if search_results['metadatas'] else []
        sources = []

        seen_urls = set()
        for metadata in metadatas:
            if not metadata:
                continue

            url = metadata.get('source_url', '')
            if url and url not in seen_urls:
                sources.append({
                    'url': url,
                    'title': metadata.get('title', 'Untitled')
                })
                seen_urls.add(url)

        return sources

    def get_stats(self) -> Dict:
        """Get statistics about the chatbot's knowledge base."""
        return {
            "total_documents": self.vector_store.count(),
            "top_k": self.top_k,
            "model": self.llm_service.model,
            "embedding_model": self.embedding_service.model
        }


# Usage example
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()

    async def test():
        orchestrator = ChatbotOrchestrator()

        # Show stats
        stats = orchestrator.get_stats()
        print("Chatbot Stats:", stats)

        # Test query
        if stats['total_documents'] > 0:
            query = "What is this website about?"
            result = await orchestrator.process_query(query)

            print(f"\nQuery: {query}")
            print(f"Response: {result['response']}")
            print(f"Sources: {result['sources']}")
        else:
            print("\nNo documents in knowledge base. Run data ingestion first.")

    asyncio.run(test())

