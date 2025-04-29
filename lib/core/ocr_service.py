"""
OCR服务统一接口
"""
from typing import Dict, Any, Optional
from .provider_base import OCRProvider
from .provider_factory import OCRProviderFactory


class OCRService:
    """OCR服务统一接口，使用提供商模式隔离不同OCR服务的具体实现"""
    
    def __init__(self, provider_name: str = "baidu"):
        """
        初始化OCR服务
        
        Args:
            provider_name: OCR提供商名称，默认为百度
        """
        self._provider = OCRProviderFactory.create(provider_name)
    
    @property
    def provider(self) -> OCRProvider:
        """获取当前使用的OCR提供商"""
        return self._provider
    
    def change_provider(self, provider_name: str) -> None:
        """
        更换OCR提供商
        
        Args:
            provider_name: 新的提供商名称
        """
        self._provider = OCRProviderFactory.create(provider_name)
    
    def authenticate(self, **credentials) -> None:
        """
        认证OCR服务
        
        Args:
            credentials: 认证所需的凭据，根据不同提供商有所不同
        """
        # 首先验证凭据
        validated_credentials = self._provider.validate_credentials(credentials)
        
        # 使用验证后的凭据进行认证
        self._provider.authenticate(**validated_credentials)
    
    def recognize_text(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        识别图片中的文字，仅支持URL
        
        Args:
            options: 必须包含url参数的字典
            
        Returns:
            统一格式的识别结果: {"text": "识别的文本内容", "provider": "服务提供商名称"}
            即使发生错误，也会返回统一格式: {"text": "", "provider": "服务提供商名称", "error": true, "error_msg": "错误信息"}
            
        Raises:
            ValueError: 如果options中不包含url
        """
        provider_name = self._provider.provider_name
        
        try:
            # 确保options中必须有url
            if not options or "url" not in options:
                raise ValueError("必须在options中提供url参数")
                
            # 调用提供商的识别方法获取原始结果
            result = self._provider.recognize_text(None, options)
            
            # 使用提供商的format_result方法处理结果格式
            return self._provider.format_result(result)
        except Exception as e:
            # 捕获所有异常，并返回统一格式的错误信息
            error_msg = str(e)
            
            # 返回统一的错误格式
            return {
                "text": "",  # 错误情况下文本为空
                "provider": provider_name,
                "error": True,
                "error_msg": error_msg,
                "raw_response": None
            }
    
    @staticmethod
    def get_available_providers() -> list:
        """获取所有可用的OCR提供商名称"""
        return OCRProviderFactory.get_available_providers()
    
    @staticmethod
    def register_provider(name: str, provider_class: type) -> None:
        """
        注册新的OCR提供商
        
        Args:
            name: 提供商名称
            provider_class: 提供商类
        """
        OCRProviderFactory.register_provider(name, provider_class) 