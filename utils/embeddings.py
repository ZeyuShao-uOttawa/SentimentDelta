"""Utility for handling text embeddings using SentenceTransformer."""

from sentence_transformers import SentenceTransformer
from utils.logger import get_logger

logger = get_logger(__name__)

class EmbeddingManager:
    """Manages text embeddings using SentenceTransformer."""
    
    def __init__(self):
        self.embedding_model = None
    
    def setup_embeddings(self, model_name: str) -> bool:
        """Setup sentence transformer model.
        
        Args:
            model_name: Name of the SentenceTransformer model to use
            
        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            logger.info(f"Setting up embedding model: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
            logger.info("Embedding model setup successful")
            return True
        except Exception as e:
            logger.error(f"Failed to setup embedding model: {e}")
            return False
    
    def get_embeddings(self, texts):
        """Get embeddings for texts.
        
        Args:
            texts: Text or list of texts to encode
            
        Returns:
            numpy.ndarray: Embeddings for the input texts, or None if model not setup
        """
        if not self.embedding_model:
            logger.warning("Embedding model not setup")
            return None
        
        try:
            return self.embedding_model.encode(texts)
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return None

# Global embedding manager instance
_embedding_manager = None

def get_embedding_manager() -> EmbeddingManager:
    """Get the global embedding manager instance."""
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager

def setup_embeddings(model_name: str) -> bool:
    """Setup embeddings with the specified model.
    
    Args:
        model_name: Name of the SentenceTransformer model to use
        
    Returns:
        bool: True if setup successful, False otherwise
    """
    return get_embedding_manager().setup_embeddings(model_name)

def get_embeddings(texts):
    """Get embeddings for texts.
    
    Args:
        texts: Text or list of texts to encode
        
    Returns:
        numpy.ndarray: Embeddings for the input texts, or None if model not setup
    """
    return get_embedding_manager().get_embeddings(texts)