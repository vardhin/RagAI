import PyPDF2
from typing import List
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter

class PDFProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                    
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
        
        return text
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', ' ', text)
        
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks for processing"""
        chunks = self.text_splitter.split_text(text)
        return [chunk.strip() for chunk in chunks if len(chunk.strip()) > 50]
    
    def extract_and_chunk(self, pdf_path: str) -> List[str]:
        """Complete pipeline: extract, clean, and chunk PDF text"""
        # Extract text
        raw_text = self.extract_text_from_pdf(pdf_path)
        
        # Clean text
        cleaned_text = self.clean_text(raw_text)
        
        # Chunk text
        chunks = self.chunk_text(cleaned_text)
        
        return chunks