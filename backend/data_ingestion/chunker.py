"""
Text chunking for optimal embedding and retrieval.
"""
from typing import List, Dict
import tiktoken


class TextChunker:
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        encoding_name: str = "cl100k_base"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception:
            # Fallback to approximate token counting
            self.encoding = None
            print("Warning: tiktoken encoding not available, using approximate token counting")

    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Split text into chunks with metadata."""
        if not text or not text.strip():
            return []

        if self.encoding:
            tokens = self.encoding.encode(text)
            chunks = []

            start = 0
            while start < len(tokens):
                end = start + self.chunk_size
                chunk_tokens = tokens[start:end]
                chunk_text = self.encoding.decode(chunk_tokens)

                chunk_data = {
                    'text': chunk_text,
                    'metadata': metadata or {},
                    'token_count': len(chunk_tokens)
                }

                chunks.append(chunk_data)

                # Move start with overlap
                start = end - self.chunk_overlap
        else:
            # Fallback: approximate chunking by characters
            chunks = []
            # Approximate: 1 token ≈ 4 characters
            char_chunk_size = self.chunk_size * 4
            char_overlap = self.chunk_overlap * 4

            start = 0
            while start < len(text):
                end = start + char_chunk_size
                chunk_text = text[start:end]

                chunk_data = {
                    'text': chunk_text,
                    'metadata': metadata or {},
                    'token_count': len(chunk_text) // 4  # Approximate
                }

                chunks.append(chunk_data)
                start = end - char_overlap

        return chunks

    def chunk_pages(self, pages: List[Dict]) -> List[Dict]:
        """Chunk multiple pages."""
        all_chunks = []

        for page in pages:
            metadata = {
                'source_url': page.get('url', ''),
                'title': page.get('title', 'Untitled')
            }

            content = page.get('content', '')
            if content:
                chunks = self.chunk_text(content, metadata)
                all_chunks.extend(chunks)

        return all_chunks


# CLI usage
if __name__ == "__main__":
    import json
    import sys

    # Test chunker
    chunker = TextChunker(chunk_size=500, chunk_overlap=50)

    test_text = "This is a test text. " * 100
    test_pages = [{
        'url': 'https://example.com',
        'title': 'Test Page',
        'content': test_text
    }]

    chunks = chunker.chunk_pages(test_pages)

    print(f"Created {len(chunks)} chunks")
    print(f"First chunk preview: {chunks[0]['text'][:100]}...")
    print(f"Token count: {chunks[0]['token_count']}")

