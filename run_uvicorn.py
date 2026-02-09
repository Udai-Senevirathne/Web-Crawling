"""
Windows-compatible Uvicorn runner.
Sets the correct asyncio event loop policy for Windows before starting Uvicorn.
This is necessary for Playwright (web scraper) to work correctly on Windows.
"""
import asyncio
import sys
import os

# Set Windows event loop policy before importing anything else
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("RELOAD", "False").lower() == "true"
    
    print("=" * 60)
    print("Starting Web Crawler Chatbot API")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Reload: {reload}")
    print(f"Docs: http://localhost:{port}/docs")
    print("=" * 60)
    
    uvicorn.run(
        "backend.api.main:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    main()
