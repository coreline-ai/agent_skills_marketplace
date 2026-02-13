from sentence_transformers import SentenceTransformer
from typing import Optional

# Initialize embedding model (singleton)
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        # Use a small, efficient model for now
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

def generate_embedding(text: str) -> Optional[list[float]]:
    if not text or not text.strip():
        return None
    model = get_embedding_model()
    return model.encode(text).tolist()
