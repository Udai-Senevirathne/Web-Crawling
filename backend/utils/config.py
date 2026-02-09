"""
Configuration management.
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # LLM Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # RAG Configuration
    TOP_K: int = int(os.getenv("TOP_K", "5"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))

    # Vector Store Configuration
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_STORE_TYPE", "chroma")
    CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma")
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "website_docs")

    # Pinecone Configuration
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "webdocs")

    # Database Configuration
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")

    # Scraping Configuration
    TARGET_WEBSITE_URL: str = os.getenv("TARGET_WEBSITE_URL", "")
    MAX_PAGES: int = int(os.getenv("MAX_PAGES", "100"))
    SCRAPE_DEPTH: int = int(os.getenv("SCRAPE_DEPTH", "3"))

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "./logs/chatbot.log")

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.OPENAI_API_KEY:
            print("[WARN] Warning: OPENAI_API_KEY not set")
            return False
        return True

    @classmethod
    def display(cls):
        """Display current configuration (safe values only)."""
        print("Configuration:")
        print(f"  Environment: {cls.ENVIRONMENT}")
        print(f"  API Host: {cls.API_HOST}:{cls.API_PORT}")
        print(f"  LLM Model: {cls.OPENAI_MODEL}")
        print(f"  Embedding Model: {cls.OPENAI_EMBEDDING_MODEL}")
        print(f"  Vector DB: {cls.VECTOR_DB_TYPE}")
        print(f"  Top K: {cls.TOP_K}")


# Create config instance
config = Config()


if __name__ == "__main__":
    config.display()
    if config.validate():
        print("[OK] Configuration valid")
    else:
        print("[ERROR] Configuration incomplete")

