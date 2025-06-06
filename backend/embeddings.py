from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List
import torch

class EmbeddingGenerator:
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        """Initialize with a sentence transformer model"""
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        
        # Use GPU if available
        if torch.cuda.is_available():
            self.model = self.model.to('cuda')
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        try:
            # Generate embeddings
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=True,
                batch_size=32
            )
            
            return embeddings
            
        except Exception as e:
            raise Exception(f"Error generating embeddings: {str(e)}")
    
    def generate_single_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        return self.model.encode([text], convert_to_numpy=True)[0]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by the model"""
        return self.model.get_sentence_embedding_dimension()