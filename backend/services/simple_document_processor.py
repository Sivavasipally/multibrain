"""
Document Processing Service - Text Extraction and Content Processing

Simple document processor that integrates with the existing text extraction
functionality from app_local.py.
"""

import os
from pathlib import Path
from typing import Optional

class DocumentProcessor:
    """Document processing service"""
    
    def __init__(self):
        # Try to import the existing extraction function
        try:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from app_local import extract_text_from_file
            self.extract_text_from_file = extract_text_from_file
        except ImportError:
            self.extract_text_from_file = None
    
    def extract_text(self, file_path: str) -> Optional[str]:
        """Extract text from a file"""
        if self.extract_text_from_file:
            return self.extract_text_from_file(file_path)
        else:
            # Fallback for basic text files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return None