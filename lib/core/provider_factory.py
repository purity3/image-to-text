"""
OCR提供商工厂类
"""
from typing import Dict, Type


class OCRProviderFactory:
    """OCR提供商工厂，负责创建和管理不同的OCR提供商实例"""
    
    # 提供商映射表，在导入具体提供商模块时会自动填充
    _providers = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type) -> None:
        """
        注册新的OCR提供商
        
        Args:
            name: 提供商名称
            provider_class: 提供商类
        """
        if name in cls._providers:
            raise ValueError(f"提供商 '{name}' 已经存在")
        
        cls._providers[name] = provider_class
    
    @classmethod
    def create(cls, provider_name: str):
        """
        创建指定名称的OCR提供商实例
        
        Args:
            provider_name: 提供商名称
            
        Returns:
            OCR提供商实例
            
        Raises:
            ValueError: 如果提供商不存在
        """
        if provider_name not in cls._providers:
            raise ValueError(f"未找到提供商 '{provider_name}'，可用的提供商: {list(cls._providers.keys())}")
        
        return cls._providers[provider_name]()
    
    @classmethod
    def get_available_providers(cls) -> list:
        """
        获取所有可用的提供商名称
        
        Returns:
            提供商名称列表
        """
        return list(cls._providers.keys()) 