from pathlib import Path
from typing import Optional


class DocumentProcessor:
    """文档处理基类"""

    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md'}

    def extract_text(self, file_path: Path) -> str:
        raise NotImplementedError

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """将文本切分为块，支持重叠"""
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk.strip())

            if end >= text_len:
                break
            start = end - overlap

        return [c for c in chunks if c]


class PDFProcessor(DocumentProcessor):
    """PDF文档处理"""

    def extract_text(self, file_path: Path) -> str:
        try:
            import pymupdf
            doc = pymupdf.open(str(file_path))
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            raise RuntimeError("pymupdf not installed: pip install pymupdf")


class DOCXProcessor(DocumentProcessor):
    """DOCX文档处理"""

    def extract_text(self, file_path: Path) -> str:
        try:
            from docx import Document
            doc = Document(str(file_path))
            return "\n".join([p.text for p in doc.paragraphs])
        except ImportError:
            raise RuntimeError("python-docx not installed: pip install python-docx")


class TXTProcessor(DocumentProcessor):
    """纯文本处理"""

    def extract_text(self, file_path: Path) -> str:
        return file_path.read_text(encoding='utf-8')


class MarkdownProcessor(DocumentProcessor):
    """Markdown处理"""

    def extract_text(self, file_path: Path) -> str:
        return file_path.read_text(encoding='utf-8')


def get_processor(file_path: Path) -> DocumentProcessor:
    """根据文件扩展名获取处理器"""
    ext = file_path.suffix.lower()

    processors = {
        '.pdf': PDFProcessor,
        '.docx': DOCXProcessor,
        '.txt': TXTProcessor,
        '.md': MarkdownProcessor,
    }

    processor_class = processors.get(ext)
    if not processor_class:
        raise ValueError(f"Unsupported file type: {ext}")

    return processor_class()