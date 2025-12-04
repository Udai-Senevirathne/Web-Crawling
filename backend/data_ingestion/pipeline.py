"""
Complete data ingestion pipeline.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.data_ingestion.scraper import WebScraper
from backend.data_ingestion.chunker import TextChunker
from backend.services.embeddings import EmbeddingService
from backend.services.vector_store import VectorStore
from tqdm import tqdm


class IngestionPipeline:
    def __init__(self, website_url: str, max_pages: int = 50, max_depth: int = 3):
        self.website_url = website_url
        self.scraper = WebScraper(website_url, max_pages=max_pages, max_depth=max_depth)
        self.chunker = TextChunker()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()

    async def run(self, reset: bool = False):
        """Run complete ingestion pipeline."""
        print("=" * 60)
        print("WEBSITE CONTENT INGESTION PIPELINE")
        print("=" * 60)
        print(f"Target URL: {self.website_url}")
        print(f"Max Pages: {self.scraper.max_pages}")
        print(f"Max Depth: {self.scraper.max_depth}")
        print("=" * 60)

        # Reset collection if requested
        if reset:
            print("\n[WARN] Resetting existing collection...")
            self.vector_store.reset_collection()

        # Step 1: Crawl website
        print("\n[1/4] Crawling website...")
        pages = await self.scraper.crawl()
        print(f"[OK] Crawled {len(pages)} pages")

        if not pages:
            print("[ERROR] No pages found. Check the URL and try again.")
            return

        # Step 2: Chunk text
        print("\n[2/4] Chunking text...")
        chunks = self.chunker.chunk_pages(pages)
        print(f"[OK] Created {len(chunks)} chunks")

        if not chunks:
            print("[ERROR] No chunks created. Content may be empty.")
            return

        # Step 3: Generate embeddings
        print("\n[3/4] Generating embeddings...")
        texts = [chunk['text'] for chunk in chunks]
        embeddings = []

        # Process in batches to avoid rate limits
        batch_size = 50
        total_batches = (len(texts) + batch_size - 1) // batch_size

        with tqdm(total=len(texts), desc="Embedding progress") as pbar:
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                batch_embeddings = self.embedding_service.generate_embeddings_batch(batch)
                embeddings.extend(batch_embeddings)
                pbar.update(len(batch))

                # Small delay to respect rate limits
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.5)

        print(f"[OK] Generated {len(embeddings)} embeddings")

        # Step 4: Store in vector database
        print("\n[4/4] Storing in vector database...")
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [chunk['metadata'] for chunk in chunks]

        try:
            self.vector_store.add_documents(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            print(f"[OK] Stored {len(chunks)} documents in vector database")
        except Exception as e:
            print(f"[ERROR] Error storing documents: {e}")
            return

        # Summary
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE!")
        print("=" * 60)
        print(f"Pages crawled:       {len(pages)}")
        print(f"Chunks created:      {len(chunks)}")
        print(f"Embeddings generated: {len(embeddings)}")
        print(f"Total documents:     {self.vector_store.count()}")
        print("=" * 60)
        print("\nYour chatbot is ready to answer questions!")


# CLI
if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    parser = argparse.ArgumentParser(description='Ingest website content for chatbot')
    parser.add_argument('--url', required=True, help='Website URL to crawl')
    parser.add_argument('--max-pages', type=int, default=50, help='Maximum pages to crawl')
    parser.add_argument('--max-depth', type=int, default=3, help='Maximum crawl depth')
    parser.add_argument('--reset', action='store_true', help='Reset existing collection')
    args = parser.parse_args()

    # Verify API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please set it in your .env file or environment")
        sys.exit(1)

    pipeline = IngestionPipeline(
        args.url,
        max_pages=args.max_pages,
        max_depth=args.max_depth
    )

    try:
        asyncio.run(pipeline.run(reset=args.reset))
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

