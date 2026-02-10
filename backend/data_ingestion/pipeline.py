"""
Complete data ingestion pipeline.
"""
import asyncio
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

from backend.data_ingestion.scraper import WebScraper
from backend.data_ingestion.chunker import TextChunker
from backend.services.embeddings import EmbeddingService
from backend.services.vector_store import VectorStore


class IngestionPipeline:
    def __init__(self, website_url: str, max_pages: int = 50, max_depth: int = 3, client_id: str | None = None, job_id: str | None = None):
        self.website_url = website_url
        self.scraper = WebScraper(website_url, max_pages=max_pages, max_depth=max_depth) if website_url else None
        self.chunker = TextChunker()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.client_id = client_id
        self.job_id = job_id

    async def run(self, reset: bool = False, files: list[str] | None = None):
        """Run complete ingestion pipeline."""
        logger.info("=" * 60)
        logger.info("WEBSITE CONTENT INGESTION PIPELINE")
        logger.info("=" * 60)
        if self.website_url:
            logger.info("Target URL: %s", self.website_url)
        if self.scraper:
            logger.info("Max Pages: %s", self.scraper.max_pages)
            logger.info("Max Depth: %s", self.scraper.max_depth)
        if self.client_id:
            logger.info("Client ID: %s", self.client_id)
        logger.info("=" * 60)

        # Reset collection if requested
        if reset:
            logger.warning("Resetting existing collection...")
            self.vector_store.reset_collection()

        # Step 1: Crawl website or process uploaded files
        pages = []
        if files and len(files) > 0:
            logger.info("[1/4] Processing uploaded files...")
            for fp in files:
                try:
                    text = self._extract_text_from_file(fp)
                    if text and text.strip():
                        pages.append({
                            'url': f'file://{fp}',
                            'title': Path(fp).name,
                            'content': text
                        })
                        logger.info("[OK] Extracted file: %s", fp)
                except Exception as e:
                    logger.warning("Failed to extract %s: %s", fp, e)
            logger.info("[OK] Processed %d uploaded files", len(pages))
        elif self.scraper:
            logger.info("[1/4] Crawling website...")
            pages = await self.scraper.crawl()
            logger.info("[OK] Crawled %d pages", len(pages))
        else:
            logger.error("No URL or files provided.")
            return

        if not pages:
            logger.error("No pages or files found. Check inputs and try again.")
            return

        # Step 2: Chunk text
        logger.info("[2/4] Chunking text...")
        if self.client_id:
            extra_meta = {"client_id": self.client_id}
        else:
            extra_meta = {}
            
        if self.job_id:
            extra_meta["job_id"] = self.job_id
            
        chunks = self.chunker.chunk_pages(pages, extra_metadata=extra_meta)
        logger.info("[OK] Created %d chunks", len(chunks))

        if not chunks:
            logger.error("No chunks created. Content may be empty.")
            return

        # Step 3: Generate embeddings
        logger.info("[3/4] Generating embeddings...")
        texts = [chunk['text'] for chunk in chunks]
        embeddings = []

        # Process in batches to avoid memory issues
        batch_size = 50
        
        try:
            from tqdm import tqdm
            with tqdm(total=len(texts), desc="Embedding progress") as pbar:
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i+batch_size]
                    batch_embeddings = self.embedding_service.generate_embeddings_batch(batch)
                    embeddings.extend(batch_embeddings)
                    pbar.update(len(batch))
                    
                    # Small delay to avoid rate limits
                    if i + batch_size < len(texts):
                        await asyncio.sleep(0.1)
        except ImportError:
            # tqdm not available, use simple progress
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                batch_embeddings = self.embedding_service.generate_embeddings_batch(batch)
                embeddings.extend(batch_embeddings)
                logger.info("  Progress: %d/%d", min(i + batch_size, len(texts)), len(texts))

        logger.info("[OK] Generated %d embeddings", len(embeddings))

        # Step 4: Store in vector database
        logger.info("[4/4] Storing in vector database...")
        # Use UUID-based IDs to prevent collisions between crawl jobs
        import uuid
        batch_id = str(uuid.uuid4())[:8]  # Short unique prefix for this batch
        ids = [f"{self.client_id}_{batch_id}_{i}" if self.client_id else f"{batch_id}_{i}" for i in range(len(chunks))]
        metadatas = [chunk['metadata'] for chunk in chunks]

        try:
            self.vector_store.add_documents(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info("[OK] Stored %d documents in vector database", len(chunks))
        except Exception as e:
            logger.error("Error storing documents: %s", e)
            return

        # Summary
        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETE!")
        logger.info("=" * 60)
        logger.info("Pages crawled:       %d", len(pages))
        logger.info("Chunks created:      %d", len(chunks))
        logger.info("Embeddings generated: %d", len(embeddings))
        logger.info("Total documents:     %d", self.vector_store.count())
        logger.info("=" * 60)
        logger.info("Your chatbot is ready to answer questions!")

    def _extract_text_from_file(self, path: str) -> str:
        """Extract text from a file. Supports PDF via PyPDF2 if available; otherwise tries to read plain text."""
        p = Path(path)
        suffix = p.suffix.lower()
        
        if suffix == '.pdf':
            try:
                # Lazy import PyPDF2 if available
                import PyPDF2
                text_parts = []
                with open(p, 'rb') as fh:
                    reader = PyPDF2.PdfReader(fh)
                    for page in reader.pages:
                        try:
                            page_text = page.extract_text() or ''
                        except Exception:
                            page_text = ''
                        text_parts.append(page_text)
                return '\n'.join(text_parts)
            except ImportError:
                logger.warning('PyPDF2 not installed; skipping PDF extraction for %s', path)
                return ''
            except Exception as e:
                logger.warning('Error extracting PDF %s: %s', path, e)
                return ''
        else:
            # Try to read as plain text
            try:
                with open(p, 'r', encoding='utf-8') as fh:
                    return fh.read()
            except Exception:
                try:
                    with open(p, 'r', encoding='latin-1') as fh:
                        return fh.read()
                except Exception:
                    return ''


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
    parser.add_argument('--client-id', type=str, default=None, help='Client ID for tenant isolation')
    args = parser.parse_args()

    pipeline = IngestionPipeline(
        args.url,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        client_id=args.client_id
    )

    try:
        asyncio.run(pipeline.run(reset=args.reset))
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user")
    except Exception as e:
        logger.error("Pipeline failed: %s", e, exc_info=True)
