"""
Test suite for chatbot services.
"""
import pytest
from backend.services.chatbot_orchestrator import ChatbotOrchestrator
from backend.data_ingestion.chunker import TextChunker


def test_text_chunker():
    """Test text chunking functionality."""
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)

    test_text = "This is a test sentence. " * 50
    test_page = {
        'url': 'https://test.com',
        'title': 'Test Page',
        'content': test_text
    }

    chunks = chunker.chunk_pages([test_page])

    assert len(chunks) > 0, "Should create at least one chunk"
    assert all('text' in chunk for chunk in chunks), "All chunks should have text"
    assert all('metadata' in chunk for chunk in chunks), "All chunks should have metadata"
    assert all(chunk['metadata']['source_url'] == 'https://test.com' for chunk in chunks)


def test_chunker_with_empty_content():
    """Test chunker with empty content."""
    chunker = TextChunker()

    empty_page = {
        'url': 'https://test.com',
        'title': 'Empty Page',
        'content': ''
    }

    chunks = chunker.chunk_pages([empty_page])
    assert len(chunks) == 0, "Should not create chunks for empty content"


@pytest.mark.asyncio
async def test_orchestrator_stats():
    """Test chatbot orchestrator stats."""
    orchestrator = ChatbotOrchestrator()
    stats = orchestrator.get_stats()

    assert 'total_documents' in stats
    assert 'top_k' in stats
    assert 'model' in stats
    assert isinstance(stats['total_documents'], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

