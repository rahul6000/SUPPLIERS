# PDF text extraction
import pdfplumber
import os

def extract_text_from_pdf(file_path):
    """Extract text from PDF file with proper error handling"""
    # Validate input
    if not file_path:
        raise ValueError("File path cannot be None or empty")
    
    if not isinstance(file_path, str):
        raise TypeError(f"File path must be a string, got {type(file_path)}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    if not file_path.lower().endswith('.pdf'):
        raise ValueError(f"File must be a PDF: {file_path}")
    
    try:
        all_text = ""
        with pdfplumber.open(file_path) as pdf:
            if not pdf.pages:
                raise ValueError("PDF file appears to be empty")
            
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    all_text += page_text + "\n"
        
        if not all_text.strip():
            raise ValueError("No text could be extracted from PDF")
            
        return all_text
        
    except Exception as e:
        if isinstance(e, (ValueError, FileNotFoundError, TypeError)):
            raise
        else:
            raise RuntimeError(f"Failed to extract text from PDF: {str(e)}")
