"""
OCR提供商抽象基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class OCRProvider(ABC):
    """OCR服务提供商的抽象基类"""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """返回提供商名称"""
        pass
    
    def validate_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证认证凭据是否有效，并返回处理后的凭据
        
        Args:
            credentials: 原始认证凭据，可能包含token、client_id、client_secret等
            
        Returns:
            处理后的凭据，用于认证方法
            
        Raises:
            ValueError: 如果凭据无效或不完整
        """
        # 基类提供默认实现，子类应该重写此方法以提供特定的验证逻辑
        return credentials
    
    @abstractmethod
    def authenticate(self, **credentials) -> None:
        """
        认证OCR服务
        
        Args:
            credentials: 认证所需的凭据
        """
        pass
    
    @abstractmethod
    def recognize_text(self, image_data: Optional[bytes], options: Dict[str, Any]) -> Dict[str, Any]:
        """
        识别图片中的文字
        
        Args:
            image_data: 图片的二进制数据，现在总是为None，保留此参数是为了向后兼容
            options: 必须包含url参数
            
        Returns:
            识别结果字典
        """
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        """
        检查是否已经通过认证
        
        Returns:
            是否已认证
        """
        pass
    
    def format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        将原始识别结果格式化为统一格式
        
        Args:
            result: 原始识别结果
            
        Returns:
            统一格式的结果: {"text": "识别的文本内容", "provider": "服务提供商名称", "raw_response": 原始响应}
        """
        # 检查结果是否包含错误信息
        if isinstance(result, dict) and ("error_code" in result or "error_msg" in result):
            has_error = result.get("error_code", 0) != 0 or result.get("error_msg", "")
            if has_error:
                return {
                    "text": "",
                    "provider": self.provider_name,
                    "error": True,
                    "error_msg": result.get("error_msg", "未知错误"),
                    "error_code": result.get("error_code", -1),
                    "raw_response": result
                }
        
        # 没有错误，提供默认的成功结果格式
        return {
            "text": "",  # 默认为空文本，子类应重写此方法提供实际文本
            "provider": self.provider_name,
            "error": False,
            "raw_response": result
        } 