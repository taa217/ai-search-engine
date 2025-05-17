import os
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # API Settings
    PORT: int = 8000
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # LLM Settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    CLAUDE_API_KEY: Optional[str] = os.getenv("CLAUDE_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "google")  # Options: openai, google, anthropic
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash-preview-04-17")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.2"))
    
    # Vector DB Settings
    VECTOR_DB: str = os.getenv("VECTOR_DB", "pinecone")  # Options: pinecone, weaviate, qdrant, faiss
    PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: Optional[str] = os.getenv("PINECONE_ENVIRONMENT")
    PINECONE_INDEX: str = os.getenv("PINECONE_INDEX", "nexus-search")
    WEAVIATE_URL: Optional[str] = os.getenv("WEAVIATE_URL")
    WEAVIATE_API_KEY: Optional[str] = os.getenv("WEAVIATE_API_KEY")
    
    # Embedding Settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # Search Settings
    DEFAULT_MAX_RESULTS: int = 10
    DEFAULT_SEARCH_DEPTH: int = 4
    
    # Web Search API Keys
    SERPER_API_KEY: Optional[str] = os.getenv("SERPER_API_KEY")
    SERP_API_KEY: Optional[str] = os.getenv("SERP_API_KEY")
    GOOGLE_CSE_ID: Optional[str] = os.getenv("GOOGLE_CSE_ID")
    
    # Caching
    ENABLE_CACHING: bool = os.getenv("ENABLE_CACHING", "True").lower() == "true"
    CACHE_EXPIRY: int = int(os.getenv("CACHE_EXPIRY", "86400"))  # 24 hours in seconds
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT: int = int(os.getenv("RATE_LIMIT", "50"))  # requests per minute
    
    # Security
    # Parse ALLOWED_ORIGINS from space-delimited string
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        origins = os.getenv("ALLOWED_ORIGINS", "*")
        if origins == "*":
            return ["*"]
        return origins.split()
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
