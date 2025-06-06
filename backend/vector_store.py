import sqlite3
import numpy as np
import pickle
from typing import List, Dict
import uuid

class VectorStore:
    def __init__(self, db_path: str = "vector_store.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    document_hash TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    chunk_count INTEGER NOT NULL
                )
            """)
            
            # Chunks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
                )
            """)
            
            # Create indices for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_hash ON documents (document_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_id ON chunks (document_id)")
            
            conn.commit()
    
    def document_exists(self, document_hash: str) -> bool:
        """Check if document already exists"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM documents WHERE document_hash = ?", (document_hash,))
            return cursor.fetchone() is not None
    
    def store_document(self, document_hash: str, filename: str, chunks: List[str], embeddings: np.ndarray) -> str:
        """Store document and its embeddings"""
        document_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Store document metadata
            cursor.execute("""
                INSERT INTO documents (id, document_hash, filename, chunk_count)
                VALUES (?, ?, ?, ?)
            """, (document_id, document_hash, filename, len(chunks)))
            
            # Store chunks and embeddings
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = str(uuid.uuid4())
                embedding_blob = pickle.dumps(embedding)
                
                cursor.execute("""
                    INSERT INTO chunks (id, document_id, chunk_index, content, embedding)
                    VALUES (?, ?, ?, ?, ?)
                """, (chunk_id, document_id, i, chunk, embedding_blob))
            
            conn.commit()
        
        return document_id
    
    def search_similar(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict]:
        """Search for similar chunks using cosine similarity"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all chunks with their embeddings
            cursor.execute("""
                SELECT c.id, c.content, c.embedding, c.document_id, d.filename
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
            """)
            
            results = []
            for row in cursor.fetchall():
                chunk_id, content, embedding_blob, doc_id, filename = row
                stored_embedding = pickle.loads(embedding_blob)
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, stored_embedding)
                
                results.append({
                    'chunk_id': chunk_id,
                    'content': content,
                    'similarity': float(similarity),
                    'document_id': doc_id,
                    'filename': filename
                })
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
        
        return dot_product / (norm_vec1 * norm_vec2)
    
    def list_documents(self) -> List[Dict]:
        """List all stored documents"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, upload_date, chunk_count
                FROM documents
                ORDER BY upload_date DESC
            """)
            
            documents = []
            for row in cursor.fetchall():
                documents.append({
                    'id': row[0],
                    'filename': row[1],
                    'upload_date': row[2],
                    'chunk_count': row[3]
                })
            
            return documents
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if document exists
            cursor.execute("SELECT 1 FROM documents WHERE id = ?", (document_id,))
            if not cursor.fetchone():
                return False
            
            # Delete chunks (will cascade due to foreign key)
            cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            conn.commit()
            
            return True