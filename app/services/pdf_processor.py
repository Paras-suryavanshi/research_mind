import io
import requests
import PyPDF2
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    
    @classmethod
    def extract_text_from_url(cls, pdf_url, max_chars=15000):
        """
        Downloads a PDF from a URL in memory and extracts text.
        Truncates the text to max_chars to avoid overflowing LLM context windows.
        """
        if not pdf_url:
            return None
            
        try:
            headers = {
                'User-Agent': 'ResearchMind/1.0 (mailto:admin@researchmind.com)'
            }
            response = requests.get(pdf_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            pdf_file = io.BytesIO(response.content)
            reader = PyPDF2.PdfReader(pdf_file)
            
            extracted_text = ""
            for i in range(len(reader.pages)):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
                    
                if len(extracted_text) >= max_chars:
                    extracted_text = extracted_text[:max_chars] + "... [Text truncated for processing]"
                    break
                    
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract PDF from {pdf_url}: {str(e)}")
            return None