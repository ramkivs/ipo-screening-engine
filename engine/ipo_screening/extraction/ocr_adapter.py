"""OCR fallback interface and scanned page detection.

Technical Design v1.5 s3.2, s15:
  Native PDF extraction is the primary path. Scanned/image pages require a
  controlled OCR fallback that preserves extraction_method = OCR, provenance
  and confidence, and fails closed on unreadable output.
"""

from __future__ import annotations

import shutil
import subprocess
from abc import ABC, abstractmethod
from typing import Optional


def detect_scanned_page(text: Optional[str], threshold: int = 50) -> bool:
    """Return True if the page appears to be a scanned image (insufficient native text)."""
    if text is None:
        return True
    return len(text.strip()) < threshold


class OcrAdapter(ABC):
    """Abstract interface for local/offline OCR extraction."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the underlying OCR engine/binary is operational."""

    @abstractmethod
    def ocr_image_bytes(self, image_bytes: bytes) -> str:
        """Extract text from raw image bytes."""


class TesseractOcrAdapter(OcrAdapter):
    """Adapter executing local tesseract binary if installed."""

    def __init__(self, binary_path: Optional[str] = None) -> None:
        self.binary_path = binary_path or shutil.which("tesseract")

    def is_available(self) -> bool:
        return bool(self.binary_path and shutil.which(self.binary_path))

    def ocr_image_bytes(self, image_bytes: bytes) -> str:
        if not self.is_available():
            return ""
        try:
            proc = subprocess.run(
                [self.binary_path, "stdin", "stdout", "--oem", "1", "-l", "eng"],
                input=image_bytes,
                capture_output=True,
                check=False,
                timeout=15,
            )
            return proc.stdout.decode("utf-8", errors="ignore")
        except Exception:
            return ""


class NoOpOcrAdapter(OcrAdapter):
    """Fallback adapter when no OCR engine is present in the environment."""

    def is_available(self) -> bool:
        return False

    def ocr_image_bytes(self, image_bytes: bytes) -> str:
        return ""
