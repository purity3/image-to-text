"""
OCR提供商实现
"""
# 注册所有提供商
from .baidu import BaiduOCRProvider
from .aliyun import AliyunOCRProvider
from .huawei import HuaweiOCRProvider

# 导入核心组件注册提供商
from ..core.provider_factory import OCRProviderFactory

# 注册提供商
OCRProviderFactory.register_provider("baidu", BaiduOCRProvider)
OCRProviderFactory.register_provider("aliyun", AliyunOCRProvider)
OCRProviderFactory.register_provider("huawei", HuaweiOCRProvider)

__all__ = [
    'BaiduOCRProvider',
    'AliyunOCRProvider',
    'HuaweiOCRProvider'
] 