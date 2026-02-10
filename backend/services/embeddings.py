"""
Generate embeddings for text chunks.
Supports OpenAI, Google, and local HuggingFace embeddings.
"""
from typing import List
import os
import time
import logging

logger = logging.getLogger(__name__)

# Global model cache to avoid reloading
_local_model = None

def get_local_model():
    """Lazy load the local embedding model."""
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer
        _local_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _local_model


class EmbeddingService:
    def __init__(self):
        self.provider = os.getenv("EMBEDDING_PROVIDER", os.getenv("LLM_PROVIDER", "local")).lower()
        self.max_retries = 3
        self.retry_delay = 2

        # Default to local embeddings for free usage
        if self.provider == "local" or self.provider == "groq":
            # Groq doesn't have embeddings, use local (lazy loaded)
            self.provider = "local"
            self.model = None  # Will be loaded on first use
        elif self.provider == "google":
            import google.generativeai as genai
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is not set")
            genai.configure(api_key=api_key)
            self.model = os.getenv("GOOGLE_EMBEDDING_MODEL", "models/embedding-001")
        else:  # openai
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            self.client = OpenAI(api_key=api_key)
            self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        for attempt in range(self.max_retries):
            try:
                if self.provider == "local":
                    model = get_local_model()
                    embedding = model.encode(text)
                    return embedding.tolist()
                elif self.provider == "google":
                    import google.generativeai as genai
                    result = genai.embed_content(
                        model=self.model,
                        content=text,
                        task_type="retrieval_document"
                    )
                    return result['embedding']
                else:  # openai
                    response = self.client.embeddings.create(
                        model=self.model,
                        input=text
                    )
                    return response.data[0].embedding
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning("Error generating embedding (attempt %d): %s", attempt + 1, e)
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches."""
        if not texts:
            return []

        # For local embeddings, process all at once (much faster)
        if self.provider == "local":
            model = get_local_model()
            embeddings = model.encode(texts)
            return [e.tolist() for e in embeddings]

        all_embeddings = []

        # Process in batches to respect API limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            for attempt in range(self.max_retries):
                try:
                    if self.provider == "google":
                        import google.generativeai as genai
                        result = genai.embed_content(
                            model=self.model,
                            content=batch,
                            task_type="retrieval_document"
                        )
                        batch_embeddings = result['embedding'] if isinstance(result['embedding'][0], list) else [result['embedding']]
                        all_embeddings.extend(batch_embeddings)
                    else:  # openai
                        response = self.client.embeddings.create(
                            model=self.model,
                            input=batch
                        )
                        batch_embeddings = [item.embedding for item in response.data]
                        all_embeddings.extend(batch_embeddings)
                    break
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        logger.warning("Error in batch %d (attempt %d): %s", i//batch_size + 1, attempt + 1, e)
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        logger.error("Failed to process batch %d: %s", i//batch_size + 1, e)
                        # Add None placeholders for failed batch
                        all_embeddings.extend([None] * len(batch))

        return all_embeddings


# Usage example
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    service = EmbeddingService()

    # Test single embedding
    text = "Hello, this is a test sentence for embedding."
    embedding = service.generate_embedding(text)
    print(f"[OK] Generated embedding with dimension: {len(embedding)}")

    # Test batch
    texts = ["First text", "Second text", "Third text"]
    embeddings = service.generate_embeddings_batch(texts)
    print(f"[OK] Generated {len(embeddings)} embeddings")

