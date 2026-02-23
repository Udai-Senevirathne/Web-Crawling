"""
Main chatbot orchestration logic (RAG pipeline).
"""
import logging
from .embeddings import EmbeddingService
from .vector_store import VectorStore
from .llm_service import LLMService
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)


class ChatbotOrchestrator:
    def __init__(self):
        self.top_k = int(os.getenv("TOP_K", "5"))
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "2.0"))

        try:
            self.embedding_service = EmbeddingService()
        except Exception as e:
            logger.warning("EmbeddingService init failed: %s", e)
            self.embedding_service = None

        try:
            self.vector_store = VectorStore()
        except Exception as e:
            logger.warning("VectorStore init failed: %s", e)
            self.vector_store = None

        try:
            self.llm_service = LLMService()
        except Exception as e:
            logger.warning("LLMService init failed: %s", e)
            self.llm_service = None

    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        client_id: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> Dict:
        """Process user query and generate response using RAG pipeline.
        
        Args:
            query: The user's question
            session_id: Optional session ID for conversation tracking
            conversation_history: Optional list of previous messages
            client_id: Optional client ID for tenant isolation (None = search all)
            system_prompt: Optional system prompt to override default behavior
        """
        logger.info("Processing query: %s...", query[:50])
        if client_id:
            logger.info("  Filtering by client_id: %s", client_id)

        # Step 1: Generate query embedding
        query_embedding = None
        if self.embedding_service is None:
            logger.warning("EmbeddingService unavailable, skipping vector search")
        else:
            try:
                query_embedding = self.embedding_service.generate_embedding(query)
            except Exception as e:
                logger.error("Error generating embedding: %s", e)

        # Step 2: Search vector store for relevant documents
        # Only apply where filter if client_id is provided
        where_clause = {"client_id": client_id} if client_id else None
        search_results = {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

        if self.vector_store is None or query_embedding is None:
            logger.warning("VectorStore/embedding unavailable, answering without RAG context")
        else:
            try:
                search_results = self.vector_store.search(
                    query_embedding=query_embedding,
                    top_k=self.top_k,
                    where=where_clause
                )
            except Exception as e:
                logger.error("Error searching vector store: %s", e)

        # Step 3: Prepare context from retrieved documents
        context = self._prepare_context(search_results)
        sources = self._extract_sources(search_results)

        # Check if we have relevant context
        if not context or context.strip() == "":
            context = "No relevant information found in the knowledge base."

        # Step 4: Generate response using LLM
        if self.llm_service is None:
            response = "The LLM service is not configured. Please set the required API keys (GROQ_API_KEY or GOOGLE_API_KEY) in your environment."
        else:
            try:
                response = self.llm_service.generate_response(
                    query=query,
                    context=context,
                    conversation_history=conversation_history,
                    system_prompt=system_prompt
                )
            except Exception as e:
                logger.error("Error generating LLM response: %s", e)
                response = "I apologize, but I'm having trouble generating a response right now. Please try again."

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
            # Skip if document is empty
            if not doc or not doc.strip():
                continue

            # Check distance threshold if available (lower distance = higher similarity)
            if distances and i < len(distances):
                # ChromaDB uses L2 distance - typically want distance < 2.0 for good matches
                if distances[i] > self.similarity_threshold:
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
        distances = search_results.get('distances', [[]])[0] if search_results.get('distances') else []
        sources = []

        seen_urls = set()
        for i, metadata in enumerate(metadatas):
            if not metadata:
                continue

            # Skip low-relevance results
            if distances and i < len(distances):
                if distances[i] > self.similarity_threshold:
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
        embedding_model = None
        if self.embedding_service:
            embedding_model = getattr(self.embedding_service, 'model', None)
            if embedding_model is None and getattr(self.embedding_service, 'provider', None) == 'local':
                embedding_model = 'all-MiniLM-L6-v2'

        doc_count = 0
        if self.vector_store:
            try:
                doc_count = self.vector_store.count()
            except Exception:
                pass

        return {
            "total_documents": doc_count,
            "top_k": self.top_k,
            "model": getattr(self.llm_service, 'model', 'unavailable') if self.llm_service else 'unavailable',
            "embedding_model": embedding_model
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
