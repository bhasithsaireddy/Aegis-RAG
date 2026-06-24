import sys
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors import PDFProcessor, DOCXProcessor, CSVProcessor, ImageProcessor

class TestAdvancedProcessors(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_csv_processor(self):
        print("\nTesting CSV Processor...")
        csv_path = self.temp_path / "test.csv"
        with open(csv_path, "w") as f:
            f.write("id,name,age,city\n")
            f.write("1,John Doe,30,New York\n")
            f.write("2,Jane Smith,25,Los Angeles\n")
            f.write("3,Bob Jones,40,Chicago\n")
            
        processor = CSVProcessor(rows_per_chunk=2)
        chunks = processor.process(csv_path)
        
        self.assertTrue(len(chunks) > 0)
        # Expect: Schema chunk + Data chunk 1 (2 rows) + Data chunk 2 (1 row) + Stats chunk
        print(f"  ✓ Generated {len(chunks)} chunks")
        
        types = [c.metadata.get("content_type") for c in chunks]
        self.assertIn("schema", types)
        self.assertIn("data", types)
        self.assertIn("statistics", types)
        print("  ✓ Schema, Data, and Statistics chunks present")

    @patch('src.processors.pdf_processor.fitz')
    def test_pdf_processor_init(self, mock_fitz):
        print("\nTesting PDF Processor Init...")
        # Mock fitz to avoid dependency issues if not installed
        processor = PDFProcessor(use_ocr=False)
        self.assertEqual(processor.doc_type, "pdf")
        print("  ✓ Initialized PDFProcessor")

    @patch('src.processors.docx_processor.Document')
    def test_docx_processor_init(self, mock_doc):
        print("\nTesting DOCX Processor Init...")
        processor = DOCXProcessor(use_ocr_for_images=False)
        self.assertEqual(processor.doc_type, "docx")
        print("  ✓ Initialized DOCXProcessor")

    @patch('src.processors.image_processor.ImageProcessor._get_ocr')
    def test_image_processor(self, mock_get_ocr):
        print("\nTesting Image Processor...")
        # Mock OCR to return dummy content
        mock_ocr = MagicMock()
        mock_ocr.extract_full_content.return_value = {"text": "Dummy OCR Text", "tables": []}
        mock_ocr.get_visual_description.return_value = "A dummy image description"
        mock_get_ocr.return_value = mock_ocr
        
        img_path = self.temp_path / "test.png"
        with open(img_path, "wb") as f:
            f.write(b"fake_image_data")
            
        processor = ImageProcessor(use_ocr=True, use_vision=True)
        # Mock _get_image_metadata to avoid PIL requirement for fake image
        with patch.object(processor, '_get_image_metadata', return_value={}):
            chunks = processor.process(img_path)
            
        self.assertTrue(len(chunks) > 0)
        types = [c.metadata.get("content_type") for c in chunks]
        print(f"  ✓ Generated chunks: {types}")
        self.assertIn("ocr_text", types)
        self.assertIn("visual_description", types)

if __name__ == '__main__':
    unittest.main()
