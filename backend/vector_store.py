import sqlite3
import numpy as np
import pickle
from typing import List, Dict, Optional
import uuid

class VectorStore:
    def __init__(self, db_path: str = "vector_store.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Documents table - now includes user_id
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    document_hash TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    user_id INTEGER,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    chunk_count INTEGER NOT NULL,
                    UNIQUE(document_hash, user_id)
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
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON documents (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_hash ON documents (user_id, document_hash)")
            
            conn.commit()
    
    def document_exists(self, document_hash: str, user_id: Optional[int] = None) -> bool:
        """Check if document already exists for the user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if user_id is not None:
                cursor.execute("SELECT 1 FROM documents WHERE document_hash = ? AND user_id = ?", 
                             (document_hash, user_id))
            else:
                cursor.execute("SELECT 1 FROM documents WHERE document_hash = ?", (document_hash,))
            return cursor.fetchone() is not None
    
    def store_document(self, document_hash: str, filename: str, chunks: List[str], 
                      embeddings: np.ndarray, user_id: Optional[int] = None) -> str:
        """Store document and its embeddings"""
        document_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Store document metadata
            cursor.execute("""
                INSERT INTO documents (id, document_hash, filename, user_id, chunk_count)
                VALUES (?, ?, ?, ?, ?)
            """, (document_id, document_hash, filename, user_id, len(chunks)))
            
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
    
    def search_similar(self, query_embedding: np.ndarray, top_k: int = 5, 
                      user_id: Optional[int] = None) -> List[Dict]:
        """Search for similar chunks using cosine similarity, optionally filtered by user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all chunks with their embeddings, filtered by user if specified
            if user_id is not None:
                cursor.execute("""
                    SELECT c.id, c.content, c.embedding, c.document_id, d.filename
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE d.user_id = ?
                """, (user_id,))
            else:
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
    
    def list_documents(self, user_id: Optional[int] = None) -> List[Dict]:
        """List all stored documents, optionally filtered by user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if user_id is not None:
                cursor.execute("""
                    SELECT id, filename, upload_date, chunk_count, document_hash
                    FROM documents
                    WHERE user_id = ?
                    ORDER BY upload_date DESC
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT id, filename, upload_date, chunk_count, document_hash
                    FROM documents
                    ORDER BY upload_date DESC
                """)
            
            documents = []
            for row in cursor.fetchall():
                documents.append({
                    'id': row[0],
                    'filename': row[1],
                    'upload_date': row[2],
                    'chunk_count': row[3],
                    'document_hash': row[4]
                })
            
            return documents
    
    def delete_document(self, document_id: str, user_id: Optional[int] = None) -> bool:
        """Delete a document and all its chunks, optionally checking user ownership"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if document exists and belongs to user (if user_id specified)
            if user_id is not None:
                cursor.execute("SELECT 1 FROM documents WHERE id = ? AND user_id = ?", 
                             (document_id, user_id))
            else:
                cursor.execute("SELECT 1 FROM documents WHERE id = ?", (document_id,))
            
            if not cursor.fetchone():
                return False
            
            # Delete document (chunks will cascade due to foreign key)
            cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            conn.commit()
            
            return True
    
    def get_document_by_hash(self, document_hash: str, user_id: Optional[int] = None) -> Optional[Dict]:
        """Get document by hash, optionally filtered by user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if user_id is not None:
                cursor.execute("""
                    SELECT id, filename, upload_date, chunk_count
                    FROM documents
                    WHERE document_hash = ? AND user_id = ?
                """, (document_hash, user_id))
            else:
                cursor.execute("""
                    SELECT id, filename, upload_date, chunk_count
                    FROM documents
                    WHERE document_hash = ?
                """, (document_hash,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'filename': row[1],
                    'upload_date': row[2],
                    'chunk_count': row[3]
                }
            return None
    
    def get_user_document_count(self, user_id: int) -> int:
        """Get number of documents for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents WHERE user_id = ?", (user_id,))
            return cursor.fetchone()[0]
    
    def get_user_chunk_count(self, user_id: int) -> int:
        """Get total number of chunks for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(chunk_count) FROM documents WHERE user_id = ?
            """, (user_id,))
            result = cursor.fetchone()[0]
            return result if result is not None else 0
    
    def migrate_existing_documents(self):
        """Migrate existing documents to have user_id column (for upgrading existing databases)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if user_id column exists
            cursor.execute("PRAGMA table_info(documents)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                # Add user_id column
                cursor.execute("ALTER TABLE documents ADD COLUMN user_id INTEGER")
                
                # Update unique constraint
                cursor.execute("DROP INDEX IF EXISTS idx_document_hash")
                cursor.execute("CREATE INDEX idx_document_hash ON documents (document_hash)")
                cursor.execute("CREATE INDEX idx_user_id ON documents (user_id)")
                cursor.execute("CREATE INDEX idx_user_hash ON documents (user_id, document_hash)")
                
                conn.commit()
                print("Database migrated to support user authentication")