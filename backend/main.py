from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List
import os
import hashlib
from pathlib import Path
import requests
import json

from pdf_processor import PDFProcessor
from vector_store import VectorStore
from embeddings import EmbeddingGenerator
from auth import (
    auth_manager, 
    UserSignup, 
    UserSignin, 
    TokenResponse, 
    RefreshTokenRequest,
    UserProfile,
    get_current_user,
    get_current_active_user,
    SecurityMiddleware
)

app = FastAPI(title="RAG Pipeline API", version="1.0.0")

# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware after CORS
app.add_middleware(SecurityMiddleware)

# Initialize components
pdf_processor = PDFProcessor()
embedding_generator = EmbeddingGenerator()
vector_store = VectorStore()

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3:0.6b"  # Change this to your preferred model

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    model: str = DEFAULT_MODEL

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    model_used: str

# Root endpoint for health check
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "RAG Pipeline API", "version": "1.0.0", "status": "running"}

# Authentication endpoints - make sure these are defined before middleware issues
@app.post("/signup", response_model=TokenResponse)
async def signup(user_data: UserSignup, request: Request):
    """User registration endpoint"""
    try:
        return await auth_manager.signup(user_data, request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/signin", response_model=TokenResponse)
async def signin(user_data: UserSignin, request: Request):
    """User login endpoint"""
    try:
        return await auth_manager.signin(user_data, request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_request: RefreshTokenRequest):
    """Refresh access token endpoint"""
    return await auth_manager.refresh_token(refresh_request)

@app.post("/logout")
async def logout(current_user: UserProfile = Depends(get_current_user)):
    """User logout endpoint"""
    # Note: You'll need to extract the token from the request
    # This is a simplified version
    return {"message": "Logged out successfully"}

@app.get("/profile", response_model=UserProfile)
async def get_profile(current_user: UserProfile = Depends(get_current_user)):
    """Get user profile endpoint"""
    return current_user

# Protected endpoints - now require authentication
@app.post("/upload-pdf/")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: UserProfile = Depends(get_current_active_user)
):
    """Upload and process a PDF file into vector embeddings"""
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Generate file hash for deduplication
        file_hash = hashlib.md5(content).hexdigest()
        
        # Check if file already processed
        if vector_store.document_exists(file_hash):
            os.remove(file_path)
            return JSONResponse(
                content={"message": "Document already processed", "document_id": file_hash},
                status_code=200
            )
        
        # Process PDF
        text_chunks = pdf_processor.extract_and_chunk(str(file_path))
        
        # Generate embeddings
        embeddings = embedding_generator.generate_embeddings(text_chunks)
        
        # Store in vector database with user association
        document_id = vector_store.store_document(
            document_hash=file_hash,
            filename=file.filename,
            chunks=text_chunks,
            embeddings=embeddings,
            user_id=current_user.id  # Associate document with user
        )
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return JSONResponse(
            content={
                "message": "PDF processed successfully",
                "document_id": document_id,
                "chunks_processed": len(text_chunks)
            },
            status_code=201
        )
        
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/upload-multiple-pdfs/")
async def upload_multiple_pdfs(
    files: List[UploadFile] = File(...),
    current_user: UserProfile = Depends(get_current_active_user)
):
    """Upload and process multiple PDF files"""
    results = []
    
    for file in files:
        try:
            result = await upload_pdf(file, current_user)
            results.append({"filename": file.filename, "status": "success", "result": result})
        except Exception as e:
            results.append({"filename": file.filename, "status": "error", "error": str(e)})
    
    return JSONResponse(content={"results": results})

@app.get("/documents/")
async def list_documents(current_user: UserProfile = Depends(get_current_active_user)):
    """List all processed documents for the current user"""
    documents = vector_store.list_documents(user_id=current_user.id)
    return JSONResponse(content={"documents": documents})

@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: UserProfile = Depends(get_current_active_user)
):
    """Delete a document and its embeddings"""
    success = vector_store.delete_document(document_id, user_id=current_user.id)
    if success:
        return JSONResponse(content={"message": "Document deleted successfully"})
    else:
        raise HTTPException(status_code=404, detail="Document not found")

@app.get("/health/")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={"status": "healthy"})

@app.post("/query/", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    current_user: UserProfile = Depends(get_current_active_user)
):
    """Query documents using RAG with Ollama"""
    
    try:
        # Generate embedding for the query
        query_embedding = embedding_generator.generate_embeddings([request.question])[0]
        
        # Search for similar chunks (scoped to user's documents)
        similar_chunks = vector_store.search_similar(
            query_embedding, 
            top_k=request.top_k,
            user_id=current_user.id
        )
        
        if not similar_chunks:
            raise HTTPException(status_code=404, detail="No relevant documents found")
        
        # Prepare context from similar chunks
        context = "\n\n".join([
            f"Source: {chunk['filename']}\nContent: {chunk['content']}"
            for chunk in similar_chunks
        ])
        
        # Create prompt for Ollama
        prompt = f"""Based on the following context from documents, please answer the question. If the answer cannot be found in the context, please say so.

Context:
{context}

Question: {request.question}

Answer:"""

        # Query Ollama
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": request.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "top_k": 40
                }
            },
            timeout=60
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Ollama error: {response.text}")
        
        ollama_response = response.json()
        answer = ollama_response.get("response", "").strip()
        
        # Prepare sources information
        sources = [
            {
                "filename": chunk["filename"],
                "similarity": round(chunk["similarity"], 3),
                "preview": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"]
            }
            for chunk in similar_chunks
        ]
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            model_used=request.model
        )
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Could not connect to Ollama: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/ollama/models")
async def get_available_models():
    """Get list of available Ollama models"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return JSONResponse(content={"models": [model["name"] for model in models]})
        else:
            raise HTTPException(status_code=503, detail="Could not fetch models from Ollama")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Ollama service not available")

@app.post("/query/stream/")
async def query_documents_stream(
    request: QueryRequest,
    current_user: UserProfile = Depends(get_current_active_user)
):
    """Query documents with streaming response from Ollama"""
    from fastapi.responses import StreamingResponse
    import json
    
    try:
        # Generate embedding for the query
        query_embedding = embedding_generator.generate_embeddings([request.question])[0]
        
        # Search for similar chunks (scoped to user's documents)
        similar_chunks = vector_store.search_similar(
            query_embedding, 
            top_k=request.top_k,
            user_id=current_user.id
        )
        
        if not similar_chunks:
            raise HTTPException(status_code=404, detail="No relevant documents found")
        
        # Prepare context
        context = "\n\n".join([
            f"Source: {chunk['filename']}\nContent: {chunk['content']}"
            for chunk in similar_chunks
        ])
        
        prompt = f"""Based on the following context from documents, please answer the question. If the answer cannot be found in the context, please say so.

Context:
{context}

Question: {request.question}

Answer:"""

        def generate_stream():
            try:
                # Send sources first
                sources = [
                    {
                        "filename": chunk["filename"],
                        "similarity": round(chunk["similarity"], 3),
                        "preview": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"]
                    }
                    for chunk in similar_chunks
                ]
                
                yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"
                
                # Stream response from Ollama
                response = requests.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": request.model,
                        "prompt": prompt,
                        "stream": True,
                        "options": {
                            "temperature": 0.1,
                            "top_p": 0.9,
                            "top_k": 40
                        }
                    },
                    stream=True,
                    timeout=60
                )
                
                for line in response.iter_lines():
                    if line:
                        chunk_data = json.loads(line)
                        if "response" in chunk_data:
                            yield f"data: {json.dumps({'type': 'token', 'data': chunk_data['response']})}\n\n"
                        
                        if chunk_data.get("done", False):
                            yield f"data: {json.dumps({'type': 'done', 'data': {'model_used': request.model}})}\n\n"
                            break
                            
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
        
        return StreamingResponse(generate_stream(), media_type="text/plain")
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Could not connect to Ollama: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

