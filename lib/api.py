"""
OCR功能的简易API接口
"""

from typing import Dict, Any, Optional
from .core import OCRService
import lib.providers  # 导入此模块会自动注册所有OCR提供商

def recognize_text(
    url: str,
    provider: str = "baidu",
    options: Optional[Dict[str, Any]] = None,
    credentials: Optional[Dict[str, Any]] = None,
    lang: str = "CHN_ENG",
) -> Dict[str, Any]:
    """
    识别图片中的文字

    Args:
        url: 图片URL地址
        provider: OCR提供商名称，默认为"baidu"，支持"aliyun"、"huawei"等
        options: OCR识别的可选参数
            - region: 区域信息（适用于华为云OCR）
        credentials: 认证凭据字典，包含认证所需的信息，如：
            - client_id/access_key_id: API Key/Access Key ID
            - client_secret/access_key_secret: Secret Key/Access Key Secret
            
            不同提供商的要求：
            - 百度OCR: 只需要提供client_id和client_secret，token会自动管理
            - 阿里云OCR: 需要提供access_key_id和access_key_secret
            - 华为云OCR: 需要提供access_key和secret_key，以及可选的region
        lang: 语言类型，默认为"CHN_ENG"（中英文混合）
              主要用于百度OCR的language_type参数
              可选值：
              - "CHN_ENG": 中英文混合
              - "ENG": 英文
              - "POR": 葡萄牙语
              - "FRE": 法语
              - "GER": 德语
              - "ITA": 意大利语
              - "SPA": 西班牙语
              - "RUS": 俄语
              - "JAP": 日语
              - "KOR": 韩语

    Returns:
        统一格式的OCR识别结果: {"text": "识别的文本内容", "provider": "服务提供商名称"}
        即使发生错误，也会返回统一格式: {"text": "", "provider": "服务提供商名称", "error": true, "error_msg": "错误信息"}

    Raises:
        ValueError: 如果认证凭据不足或无效
    """
    # 1. 创建OCR服务
    service = OCRService(provider)
    
    # 2. 准备credentials
    if credentials is None:
        credentials = {}
    
    # 3. 准备options，确保包含url
    if options is None:
        options = {}
    
    # 添加URL到options
    options["url"] = url
    
    # 添加language_type参数（百度OCR专用）
    if provider == "baidu" and lang:
        options["language_type"] = lang
    
    # 确保options被正确处理
    if "options" not in credentials:
        credentials["options"] = options
    else:
        # 合并options
        credentials["options"] = {**credentials.get("options", {}), **options}
    
    # 4. 认证处理 (OCRService内部会调用provider的validate_credentials方法)
    service.authenticate(**credentials)
    
    # 5. 执行OCR识别，只传入包含URL的options
    return service.recognize_text(credentials.get("options"))
