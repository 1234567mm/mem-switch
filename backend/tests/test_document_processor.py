import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from services.document_processor import (
    DocumentProcessor,
    PDFProcessor,
    DOCXProcessor,
    TXTProcessor,
    MarkdownProcessor,
    get_processor,
)


class TestDocumentProcessor:
    def test_extract_text_raises_not_implemented(self):
        processor = DocumentProcessor()
        with pytest.raises(NotImplementedError):
            processor.extract_text(Path("/fake/path.pdf"))

    def test_chunk_text_normal_case(self):
        processor = DocumentProcessor()
        text = "A" * 600
        chunks = processor.chunk_text(text, chunk_size=200, overlap=50)
        assert len(chunks) == 4

    def test_chunk_text_with_overlap(self):
        processor = DocumentProcessor()
        text = "ABCDEFGHIJ" * 100
        chunks = processor.chunk_text(text, chunk_size=10, overlap=5)
        for i in range(len(chunks) - 1):
            assert chunks[i][-5:] == chunks[i + 1][:5]

    def test_chunk_text_shorter_than_chunk_size(self):
        processor = DocumentProcessor()
        chunks = processor.chunk_text("Short text", chunk_size=500)
        assert len(chunks) == 1

    def test_chunk_text_empty_string(self):
        processor = DocumentProcessor()
        chunks = processor.chunk_text("", chunk_size=100)
        assert chunks == []

    def test_chunk_text_exact_chunk_size(self):
        processor = DocumentProcessor()
        chunks = processor.chunk_text("A" * 200, chunk_size=200)
        assert len(chunks) == 1

    def test_chunk_text_whitespace_stripping(self):
        processor = DocumentProcessor()
        chunks = processor.chunk_text("  Hello World  " * 50, chunk_size=50)
        for chunk in chunks:
            assert chunk == chunk.strip()


class TestPDFProcessor:
    def test_extract_text_success(self):
        mock_doc = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Page 1 text"
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Page 2 text"
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page1, mock_page2]))
        mock_doc.close = MagicMock()

        with patch('services.document_processor.pymupdf') as mock_pymupdf:
            mock_pymupdf.open.return_value = mock_doc
            processor = PDFProcessor()
            text = processor.extract_text(Path("/fake/file.pdf"))
            assert text == "Page 1 textPage 2 text"

    def test_extract_text_import_error(self):
        with patch('services.document_processor.pymupdf', side_effect=ImportError):
            processor = PDFProcessor()
            with pytest.raises(RuntimeError, match="pymupdf not installed"):
                processor.extract_text(Path("/fake/file.pdf"))


class TestDOCXProcessor:
    def test_extract_text_success(self):
        mock_doc = MagicMock()
        mock_doc.paragraphs = [MagicMock(text="Line 1"), MagicMock(text="Line 2")]
        with patch('services.document_processor.Document') as MockDocument:
            MockDocument.return_value = mock_doc
            processor = DOCXProcessor()
            text = processor.extract_text(Path("/fake/file.docx"))
            assert text == "Line 1\nLine 2"

    def test_extract_text_import_error(self):
        with patch('services.document_processor.Document', side_effect=ImportError):
            processor = DOCXProcessor()
            with pytest.raises(RuntimeError, match="python-docx not installed"):
                processor.extract_text(Path("/fake/file.docx"))


class TestTXTProcessor:
    def test_extract_text_success(self):
        processor = TXTProcessor()
        with patch.object(Path, 'read_text', return_value="Hello, World!"):
            text = processor.extract_text(Path("/fake/file.txt"))
            assert text == "Hello, World!"


class TestMarkdownProcessor:
    def test_extract_text_success(self):
        processor = MarkdownProcessor()
        with patch.object(Path, 'read_text', return_value="# Hello World"):
            text = processor.extract_text(Path("/fake/file.md"))
            assert text == "# Hello World"


class TestGetProcessor:
    def test_get_pdf_processor(self):
        processor = get_processor(Path("/fake/document.pdf"))
        assert isinstance(processor, PDFProcessor)

    def test_get_docx_processor(self):
        processor = get_processor(Path("/fake/document.docx"))
        assert isinstance(processor, DOCXProcessor)

    def test_get_txt_processor(self):
        processor = get_processor(Path("/fake/document.txt"))
        assert isinstance(processor, TXTProcessor)

    def test_get_md_processor(self):
        processor = get_processor(Path("/fake/document.md"))
        assert isinstance(processor, MarkdownProcessor)

    def test_get_processor_case_insensitive(self):
        processor = get_processor(Path("/fake/document.PDF"))
        assert isinstance(processor, PDFProcessor)
        processor = get_processor(Path("/fake/document.DOCX"))
        assert isinstance(processor, DOCXProcessor)

    def test_get_processor_unsupported_file_type(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            get_processor(Path("/fake/document.exe"))

    def test_get_processor_unsupported_with_dot(self):
        with pytest.raises(ValueError, match="Unsupported file type: .xyz"):
            get_processor(Path("/fake/document.xyz"))


class TestSupportedExtensions:
    def test_supported_extensions_contains_expected_types(self):
        expected = {'.pdf', '.docx', '.txt', '.md'}
        assert DocumentProcessor.SUPPORTED_EXTENSIONS == expected
