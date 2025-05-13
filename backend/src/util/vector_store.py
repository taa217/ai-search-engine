from typing import Optional, Dict, Any
from enum import Enum
import os
from langchain.schema import Document
from langchain.schema.vectorstore import VectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Pinecone, Weaviate, Qdrant, FAISS
import pinecone
from ..config import settings
from .logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

class VectorStoreType(str, Enum):
    """Supported vector store types."""
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    QDRANT = "qdrant"
    FAISS = "faiss"

def get_vector_store() -> VectorStore:
    """
    Initialize and return the appropriate vector store based on configuration.
    
    Returns:
        A VectorStore instance (Pinecone, Weaviate, Qdrant, or FAISS)
    """
    # Initialize embeddings model
    # Dynamically select embedding provider
    provider = getattr(settings, 'DEFAULT_MODEL_PROVIDER', os.getenv('DEFAULT_MODEL_PROVIDER', 'gemini')).lower()
    if provider in ('google', 'gemini'):
        embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY
        )
    else:
        embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
    
    vector_store_type = settings.VECTOR_DB.lower()
    
    try:
        if vector_store_type == VectorStoreType.PINECONE:
            return _initialize_pinecone(embeddings)
        elif vector_store_type == VectorStoreType.WEAVIATE:
            return _initialize_weaviate(embeddings)
        elif vector_store_type == VectorStoreType.QDRANT:
            return _initialize_qdrant(embeddings)
        elif vector_store_type == VectorStoreType.FAISS:
            return _initialize_faiss(embeddings)
        else:
            logger.warning(f"Unknown vector store type '{vector_store_type}', falling back to FAISS")
            return _initialize_faiss(embeddings)
    except Exception as e:
        logger.error(f"Error initializing vector store: {str(e)}")
        logger.warning("Falling back to FAISS vector store")
        return _initialize_faiss(embeddings)

def _initialize_pinecone(embeddings) -> VectorStore:
    """Initialize Pinecone vector store."""
    if not settings.PINECONE_API_KEY or not settings.PINECONE_ENVIRONMENT:
        raise ValueError("Missing Pinecone API key or environment")
    
    logger.info("Initializing Pinecone vector store")
    
    index_name = settings.PINECONE_INDEX
    
    # Check if we're using the newer Pinecone client (>=6.0) or older version
    pinecone_version = pinecone.__version__ if hasattr(pinecone, '__version__') else "unknown"
    logger.info(f"Detected Pinecone version: {pinecone_version}")
    
    try:
        # Handle newer Pinecone client (v6+)
        if hasattr(pinecone, 'Pinecone'):
            # New API style for Pinecone v6+
            pc = pinecone.Pinecone(api_key=settings.PINECONE_API_KEY, environment=settings.PINECONE_ENVIRONMENT)
            
            # Check if index exists and create if needed
            try:
                indexes = [idx['name'] for idx in pc.list_indexes()]
                if index_name not in indexes:
                    logger.info(f"Creating new Pinecone index: {index_name}")
                    pc.create_index(
                        name=index_name,
                        dimension=1536,  # For OpenAI embeddings
                        metric="cosine"
                    )
            except AttributeError:
                # Some older versions of v6 had a different API
                if not pc.list_indexes().get(index_name):
                    logger.info(f"Creating new Pinecone index: {index_name}")
                    pc.create_index(
                        name=index_name,
                        dimension=1536,
                        metric="cosine"
                    )
                    
            return Pinecone.from_existing_index(
                index_name=index_name,
                embedding=embeddings
            )
        else:
            # Handle older Pinecone client (v2.x)
    pinecone.init(
        api_key=settings.PINECONE_API_KEY,
        environment=settings.PINECONE_ENVIRONMENT
    )
    
    # Check if index exists
    if index_name not in pinecone.list_indexes():
        logger.info(f"Creating new Pinecone index: {index_name}")
        pinecone.create_index(
            name=index_name,
            dimension=1536,  # For OpenAI embeddings
            metric="cosine"
        )
    
    return Pinecone.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )
    except Exception as e:
        logger.error(f"Error initializing Pinecone: {str(e)}")
        raise

def _initialize_weaviate(embeddings) -> VectorStore:
    """Initialize Weaviate vector store."""
    if not settings.WEAVIATE_URL:
        raise ValueError("Missing Weaviate URL")
    
    logger.info("Initializing Weaviate vector store")
    
    import weaviate
    from weaviate.auth import AuthApiKey
    
    # Set up auth if API key is provided
    auth_config = None
    if settings.WEAVIATE_API_KEY:
        auth_config = AuthApiKey(api_key=settings.WEAVIATE_API_KEY)
    
    client = weaviate.Client(
        url=settings.WEAVIATE_URL,
        auth_client_secret=auth_config
    )
    
    return Weaviate(
        client=client,
        index_name="NexusSearch",
        text_key="content",
        embedding=embeddings
    )

def _initialize_qdrant(embeddings) -> VectorStore:
    """Initialize Qdrant vector store."""
    logger.info("Initializing Qdrant vector store")
    
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams
    
    # Create directory for local Qdrant storage
    collection_name = "nexus_search"
    qdrant_path = os.path.join(os.path.dirname(__file__), "..", "..", "qdrant_data")
    os.makedirs(qdrant_path, exist_ok=True)
    
    # Initialize Qdrant client
    client = QdrantClient(path=qdrant_path)
    
    # Create collection if it doesn't exist
    collections = client.get_collections().collections
    collection_names = [collection.name for collection in collections]
    
    if collection_name not in collection_names:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
    
    return Qdrant(
        client=client,
        collection_name=collection_name,
        embedding=embeddings
    )

def _initialize_faiss(embeddings) -> VectorStore:
    """Initialize FAISS vector store."""
    logger.info("Initializing FAISS vector store")
    
    # Create directory for FAISS index
    faiss_path = os.path.join(os.path.dirname(__file__), "..", "..", "faiss_index")
    os.makedirs(faiss_path, exist_ok=True)
    
    # Check if index exists
    index_file = os.path.join(faiss_path, "index.faiss")
    if os.path.exists(index_file):
        # Load existing index
        return FAISS.load_local(
            folder_path=faiss_path,
            embeddings=embeddings,
            index_name="index"
        )
    else:
        # Create new index with empty documents
        texts = ["Initial document to create the index"]
        metadatas = [{"source": "initialization"}]
        faiss_index = FAISS.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas
        )
        # Save index
        faiss_index.save_local(faiss_path, index_name="index")
        return faiss_index
