import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=str(env_path))

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "search-index")
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")
WEAVIATE_INDEX = os.getenv("WEAVIATE_INDEX", "Search")
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "search_collection")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))
VECTOR_DB = os.getenv("VECTOR_DB", "faiss").lower()

# Search Configuration
USE_QUERY_ENHANCEMENT = os.getenv("USE_QUERY_ENHANCEMENT", "true").lower() == "true"
USE_DUCKDUCKGO = os.getenv("USE_DUCKDUCKGO", "true").lower() == "true"
USE_WIKIPEDIA = os.getenv("USE_WIKIPEDIA", "true").lower() == "true"
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "20"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))
SEARCH_DEPTH = int(os.getenv("SEARCH_DEPTH", "20"))

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    # Generate a secret key if not provided
    import secrets
    SECRET_KEY = secrets.token_hex(32)

# Debug mode
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Cache settings
CACHE_EXPIRATION = int(os.getenv("CACHE_EXPIRATION", "3600"))  # 1 hour cache expiration
USE_CACHE = os.getenv("USE_CACHE", "true").lower() == "true"

# File storage configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
ALLOWED_EXTENSIONS = set(["pdf", "docx", "txt", "csv", "json"])
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB in bytes

# Timeout settings
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))  # timeout in seconds

# OAuth settings (for future use)
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET", "")
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", "logs")

# Create necessary directories
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True) 