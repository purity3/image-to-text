"""
华为云OCR提供商实现
"""
import base64
from typing import Dict, Any, Optional, List

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkocr.v1.region.ocr_region import OcrRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkocr.v1 import *

from ..core.provider_base import OCRProvider


class HuaweiOCRProvider(OCRProvider):
    """华为云OCR服务提供商的具体实现"""
    
    def __init__(self):
        self._access_key = None
        self._secret_key = None
        self._region = None
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "huawei"
    
    def validate_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证华为云OCR认证凭据是否有效
        
        Args:
            credentials: 原始认证凭据，必须包含
                - client_id/access_key: AK(Access Key)
                - client_secret/secret_key: SK(Secret Key)
                可选包含
                - region: 区域信息，默认为cn-north-4
                - options: 其他选项
            
        Returns:
            处理后的凭据，用于authenticate方法
            
        Raises:
            ValueError: 如果凭据无效或不完整
        """
        # 支持不同命名方式
        access_key = credentials.get("client_id") or credentials.get("access_key")
        secret_key = credentials.get("client_secret") or credentials.get("secret_key")
        
        if not access_key or not secret_key:
            raise ValueError("华为云OCR认证需要提供access_key(client_id)和secret_key(client_secret)")
        
        # 提取区域信息
        region = credentials.get("region", "cn-north-4")
        if credentials.get("options") and credentials["options"].get("region"):
            region = credentials["options"]["region"]
        
        return {
            "access_key": access_key,
            "secret_key": secret_key,
            "region": region
        }
    
    def authenticate(self, **credentials) -> None:
        """
        获取华为云OCR认证
        
        Args:
            credentials: 必须包含access_key(AK)、secret_key(SK)和region
        """
        if 'access_key' not in credentials or 'secret_key' not in credentials:
            raise ValueError("认证需要提供access_key(AK)和secret_key(SK)")
            
        self._access_key = credentials['access_key']
        self._secret_key = credentials['secret_key']
        # 默认使用cn-north-4区域，如果提供了其他区域则使用提供的区域
        self._region = credentials.get('region', 'cn-north-4')
        
        # 创建华为云认证对象
        hw_credentials = BasicCredentials(self._access_key, self._secret_key)
        
        # 创建OCR客户端
        try:
            self._client = OcrClient.new_builder() \
                .with_credentials(hw_credentials) \
                .with_region(OcrRegion.value_of(self._region)) \
                .build()
        except Exception as e:
            raise ValueError(f"创建华为云OCR客户端失败: {str(e)}")
    
    def is_authenticated(self) -> bool:
        return self._client is not None
    
    def recognize_text(self, image_data: Optional[bytes], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        使用华为云OCR识别图片中的文字
        
        Args:
            image_data: 图片的二进制数据，如果为None则必须在options中提供url
            options: 可选参数，必须包含url参数
            
        Returns:
            识别结果字典
        """
        if not self.is_authenticated():
            raise Exception("未认证，请先调用authenticate方法")
        
        try:
            request = RecognizeGeneralTextRequest()
            
            # 检查options
            if not options:
                options = {}
                
            # 确保有url或image_data其中之一
            if 'url' not in options and image_data is None:
                raise ValueError("必须提供url或图片数据")
                
            # 优先使用options中的url
            if 'url' in options:
                url = options['url']
                request.body = GeneralTextRequestBody(url=url)
            elif image_data:
                # 将图片数据转换为base64编码
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                request.body = GeneralTextRequestBody(image=image_base64)
            else:
                return {
                    "words_result": [],
                    "error_code": -1,
                    "error_msg": "缺少图片数据或URL",
                    "raw_response": {}
                }
            
            # 执行OCR识别
            response = self._client.recognize_general_text(request)
            
            # 解析结果
            if response and response.result and response.result.words_block_list:
                # 提取所有文本块
                words_blocks = response.result.words_block_list
                # 使用空格连接所有文本块
                all_text = " ".join([block.words for block in words_blocks if block.words])
                
                # 构建与统一格式相符的结果
                words_result = [{"words": block.words} for block in words_blocks if block.words]
                
                return {
                    "words_result": words_result,
                    "error_code": 0,
                    "error_msg": "",
                    "raw_response": {
                        "words_block_list": [
                            {
                                "words": block.words,
                                "confidence": getattr(block, "confidence", None)
                            } for block in words_blocks
                        ]
                    }
                }
            
            return {
                "words_result": [],
                "error_code": -1,
                "error_msg": "无法解析OCR结果",
                "raw_response": {}
            }
            
        except exceptions.ClientRequestException as e:
            return {
                "words_result": [],
                "error_code": e.error_code or -1,
                "error_msg": e.error_msg,
                "raw_response": {
                    "status_code": e.status_code,
                    "request_id": e.request_id,
                    "error_code": e.error_code,
                    "error_msg": e.error_msg
                }
            }
        except Exception as e:
            return {
                "words_result": [],
                "error_code": -1,
                "error_msg": str(e),
                "raw_response": {}
            }
    
    def format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        将华为云OCR原始识别结果格式化为统一格式
        
        Args:
            result: 原始识别结果
            
        Returns:
            统一格式的结果: {"text": "识别的文本内容", "provider": "华为云", "raw_response": 原始响应}
        """
        # 检查结果中是否包含错误信息
        if isinstance(result, dict):
            error_code = result.get("error_code", 0)
            error_msg = result.get("error_msg", "")
            
            if error_code != 0 or error_msg:
                return {
                    "text": "",
                    "provider": self.provider_name,
                    "error": True,
                    "error_msg": error_msg or "华为云OCR服务返回错误",
                    "error_code": error_code,
                    "raw_response": result
                }
        
        # 处理正常结果
        text = ""
        if "words_result" in result:
            # 使用空格连接而不是换行符
            text = " ".join([item.get("words", "") for item in result.get("words_result", [])])
        
        return {
            "text": text,
            "provider": self.provider_name,
            "error": False,
            "raw_response": result
        } 