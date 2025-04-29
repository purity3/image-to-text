"""
OCR服务库，提供对各种OCR服务的统一接口
"""
# 只导出OCR识别API函数
from .api import recognize_text

__all__ = [
    'recognize_text'
] 