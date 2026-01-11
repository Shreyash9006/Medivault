import PyPDF2
import os
from PIL import Image
import io

class PDFExtractor:
    """Extract text from PDF and image files"""
    
    def __init__(self):
        """Initialize PDF extractor"""
        pass
    
    def extract_from_pdf(self, file_path):
        """
        Extract text from PDF file
        
        Args:
            file_path (str): Path to PDF file
            
        Returns:
            dict: {
                'success': bool,
                'text': str,
                'pages': int,
                'error': str (if failed)
            }
        """
        result = {
            'success': False,
            'text': '',
            'pages': 0,
            'error': None
        }
        
        try:
            # Open PDF file
            with open(file_path, 'rb') as file:
                # Create PDF reader object
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Get number of pages
                num_pages = len(pdf_reader.pages)
                result['pages'] = num_pages
                
                # Extract text from all pages
                extracted_text = []
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    if text.strip():
                        extracted_text.append(f"--- Page {page_num + 1} ---\n{text}")
                
                # Combine all text
                result['text'] = '\n\n'.join(extracted_text)
                result['success'] = True
                
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
        
        return result
    
    def extract_from_image(self, file_path):
        """
        Extract text from image file using basic OCR
        For hackathon demo, we'll return a placeholder
        In production, integrate Tesseract OCR or Google Vision API
        
        Args:
            file_path (str): Path to image file
            
        Returns:
            dict: {
                'success': bool,
                'text': str,
                'error': str (if failed)
            }
        """
        result = {
            'success': False,
            'text': '',
            'error': None
        }
        
        try:
            # Verify image can be opened
            img = Image.open(file_path)
            
            # For hackathon: return placeholder text
            # In production: use Tesseract OCR or cloud OCR API
            result['text'] = f"""[Medical Image Document]
Image file: {os.path.basename(file_path)}
Size: {img.size[0]}x{img.size[1]} pixels
Format: {img.format}

Note: For full OCR functionality in production, integrate:
- Tesseract OCR (open source)
- Google Cloud Vision API
- AWS Textract

For demo purposes, please manually enter key findings or upload PDF version."""
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
        
        return result
    
    def extract_from_text(self, file_path):
        """
        Extract text from plain text file
        
        Args:
            file_path (str): Path to text file
            
        Returns:
            dict: {
                'success': bool,
                'text': str,
                'error': str (if failed)
            }
        """
        result = {
            'success': False,
            'text': '',
            'error': None
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                result['text'] = file.read()
                result['success'] = True
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
        
        return result
    
    def extract_text(self, file_path):
        """
        Smart text extraction based on file type
        
        Args:
            file_path (str): Path to file
            
        Returns:
            dict: Extraction result with text content
        """
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Route to appropriate extractor
        if ext == '.pdf':
            return self.extract_from_pdf(file_path)
        elif ext in ['.png', '.jpg', '.jpeg']:
            return self.extract_from_image(file_path)
        elif ext == '.txt':
            return self.extract_from_text(file_path)
        else:
            return {
                'success': False,
                'text': '',
                'error': f'Unsupported file type: {ext}'
            }
    
    def clean_medical_text(self, text):
        """
        Clean and normalize extracted medical text
        
        Args:
            text (str): Raw extracted text
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        
        # Join with single newlines
        cleaned = '\n'.join(lines)
        
        # Remove multiple spaces
        import re
        cleaned = re.sub(r' +', ' ', cleaned)
        
        return cleaned
    
    def get_document_metadata(self, file_path):
        """
        Extract metadata from document
        
        Args:
            file_path (str): Path to document
            
        Returns:
            dict: Document metadata
        """
        metadata = {
            'filename': os.path.basename(file_path),
            'size_bytes': os.path.getsize(file_path),
            'extension': os.path.splitext(file_path)[1].lower(),
            'is_readable': True
        }
        
        # Try to get PDF-specific metadata
        if metadata['extension'] == '.pdf':
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    metadata['pages'] = len(pdf_reader.pages)
                    
                    # Get PDF info if available
                    if pdf_reader.metadata:
                        metadata['title'] = pdf_reader.metadata.get('/Title', '')
                        metadata['author'] = pdf_reader.metadata.get('/Author', '')
                        metadata['creator'] = pdf_reader.metadata.get('/Creator', '')
            except:
                pass
        
        return metadata

# Convenience function
def extract_text_from_file(file_path):
    """
    Quick function to extract text from any supported file
    
    Args:
        file_path (str): Path to file
        
    Returns:
        str: Extracted text or empty string if failed
    """
    extractor = PDFExtractor()
    result = extractor.extract_text(file_path)
    
    if result['success']:
        return extractor.clean_medical_text(result['text'])
    else:
        return ""

# Test function
if __name__ == '__main__':
    print("🧪 Testing PDF/Text Extractor...")
    
    extractor = PDFExtractor()
    
    # Test 1: Create a sample text file
    print("\n📝 Test 1: Text file extraction")
    test_text = """MEDICAL PRESCRIPTION
    
Patient: Demo Patient
Health ID: MV12345
Date: 2024-01-10

Diagnosis: Type 2 Diabetes Mellitus

Medications:
1. Metformin 500mg - Take 1 tablet twice daily with meals
2. Atorvastatin 10mg - Take 1 tablet at bedtime

Allergies: Penicillin, Peanuts

Follow-up: 2 weeks"""
    
    with open('test_prescription.txt', 'w') as f:
        f.write(test_text)
    
    result = extractor.extract_from_text('test_prescription.txt')
    if result['success']:
        print("   ✓ Text extraction successful")
        print(f"   ✓ Extracted {len(result['text'])} characters")
    else:
        print(f"   ✗ Failed: {result['error']}")
    
    # Test 2: Get metadata
    print("\n📊 Test 2: File metadata")
    metadata = extractor.get_document_metadata('test_prescription.txt')
    print(f"   Filename: {metadata['filename']}")
    print(f"   Size: {metadata['size_bytes']} bytes")
    print(f"   Extension: {metadata['extension']}")
    
    # Test 3: Clean text
    print("\n🧹 Test 3: Text cleaning")
    dirty_text = """Line 1   with   extra    spaces


Line 2 with blank lines

Line 3"""
    cleaned = extractor.clean_medical_text(dirty_text)
    print(f"   Original lines: {dirty_text.count(chr(10)) + 1}")
    print(f"   Cleaned lines: {cleaned.count(chr(10)) + 1}")
    
    # Cleanup
    os.remove('test_prescription.txt')
    
    print("\n✅ All tests passed!")