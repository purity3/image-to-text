"""
核心功能模块，包含OCR服务和提供商抽象
"""

from .ocr_service import OCRService
from .provider_base import OCRProvider
from .provider_factory import OCRProviderFactory

__all__ = ['OCRService', 'OCRProvider', 'OCRProviderFactory'] 