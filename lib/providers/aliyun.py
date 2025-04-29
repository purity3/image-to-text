"""
阿里云OCR提供商实现
"""

import json
import base64
from typing import Dict, Any, Optional

from alibabacloud_ocr_api20210707.client import Client as ocr_api20210707Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ocr_api20210707 import models as ocr_api_20210707_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

from ..core.provider_base import OCRProvider


class AliyunOCRProvider(OCRProvider):
    """阿里云OCR服务提供商的具体实现"""

    def __init__(self):
        self._access_key_id = None
        self._access_key_secret = None
        self._client = None

    @property
    def provider_name(self) -> str:
        return "aliyun"

    def validate_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证阿里云OCR认证凭据是否有效

        Args:
            credentials: 原始认证凭据，必须包含
                - client_id/access_key_id: AccessKey ID
                - client_secret/access_key_secret: AccessKey Secret

        Returns:
            处理后的凭据，用于authenticate方法

        Raises:
            ValueError: 如果凭据无效或不完整
        """
        # 支持client_id或access_key_id命名方式
        access_key_id = credentials.get("client_id") or credentials.get("access_key_id")
        access_key_secret = credentials.get("client_secret") or credentials.get(
            "access_key_secret"
        )

        if not access_key_id or not access_key_secret:
            raise ValueError("阿里云OCR认证需要提供access_key_id和access_key_secret")

        return {"access_key_id": access_key_id, "access_key_secret": access_key_secret}

    def authenticate(self, **credentials) -> None:
        """
        获取阿里云OCR认证

        Args:
            credentials: 必须包含access_key_id和access_key_secret
        """
        if "access_key_id" not in credentials or "access_key_secret" not in credentials:
            raise ValueError("认证需要提供access_key_id和access_key_secret")

        self._access_key_id = credentials["access_key_id"]
        self._access_key_secret = credentials["access_key_secret"]

        # 创建阿里云客户端
        try:
            config = open_api_models.Config(
                access_key_id=self._access_key_id, access_key_secret=self._access_key_secret
            )
            config.endpoint = "ocr-api.cn-hangzhou.aliyuncs.com"
            self._client = ocr_api20210707Client(config)
            
            # 验证客户端是否有效
            # 对阿里云OCR的验证采用特殊方法：
            # 不进行实际API调用验证，而是假设客户端配置成功就认为验证通过
            # 这样做是因为阿里云OCR API必须提供图像数据才能正常调用
            
            # 如果没有抛出异常，说明客户端创建成功，认为认证有效
            # 实际认证状态将在首次调用API时验证
            
            # 即使这里认证成功，在实际调用过程中如果凭据无效，会在调用时抛出异常
            # 通过is_authenticated()方法检查客户端是否已创建

        except Exception as e:
            # 处理配置和创建客户端时的异常
            self._client = None
            error_message = getattr(e, "message", str(e))
            raise ValueError(f"阿里云OCR客户端创建失败: {error_message}")

    def is_authenticated(self) -> bool:
        return self._client is not None

    def recognize_text(
        self, image_data: Optional[bytes], options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        使用阿里云OCR识别图片中的文字

        Args:
            image_data: 图片的二进制数据，如果为None则必须在options中提供url
            options: 可选参数，必须包含url参数

        Returns:
            识别结果字典
        """
        if not self.is_authenticated():
            raise Exception("未认证，请先调用authenticate方法")

        runtime = util_models.RuntimeOptions()

        try:
            # 检查options
            if not options:
                options = {}

            # 确保有url或image_data其中之一
            if "url" not in options and image_data is None:
                raise ValueError("必须提供url或图片数据")

            # 优先使用options中的url
            if "url" in options:
                url = options["url"]
                recognize_request = ocr_api_20210707_models.RecognizeGeneralRequest(url)
            elif image_data:
                # 将图片数据转换为base64编码
                image_base64 = base64.b64encode(image_data).decode("utf-8")
                # 使用body参数传递图片数据
                recognize_request = ocr_api_20210707_models.RecognizeGeneralRequest(
                    body=image_base64
                )
            else:
                return {
                    "words_result": [],
                    "error_code": -1,
                    "error_msg": "缺少图片数据或URL",
                    "raw_response": {},
                }

            # 执行OCR识别
            response = self._client.recognize_general_with_options(
                recognize_request, runtime
            )

            # 解析结果
            if response and response.body and response.body.data:
                body_data = response.body.data
                result_data = json.loads(body_data)
                return {
                    "words_result": [{"words": result_data.get("content", "")}],
                    "error_code": 0,
                    "error_msg": "",
                    "raw_response": result_data,
                }

            return {
                "words_result": [],
                "error_code": -1,
                "error_msg": "无法解析OCR结果",
                "raw_response": {},
            }

        except Exception as e:
            error_message = getattr(e, "message", str(e))
            return {
                "words_result": [],
                "error_code": -1,
                "error_msg": error_message,
                "raw_response": {},
            }

    def format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        将阿里云OCR原始识别结果格式化为统一格式

        Args:
            result: 原始识别结果

        Returns:
            统一格式的结果: {"text": "识别的文本内容", "provider": "阿里云", "raw_response": 原始响应}
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
                    "error_msg": error_msg or "阿里云OCR服务返回错误",
                    "error_code": error_code,
                    "raw_response": result,
                }

        # 处理正常结果
        text = ""

        # 处理阿里云OCR特有的结果格式
        if "words_result" in result and result["words_result"]:
            # 使用空格替代换行符
            text = " ".join(
                [item.get("words", "") for item in result.get("words_result", [])]
            )
        elif "raw_response" in result and isinstance(result["raw_response"], dict):
            # 阿里云OCR内容通常位于raw_response中的content字段
            text = result["raw_response"].get("content", "")

        return {
            "text": text,
            "provider": self.provider_name,
            "error": False,
            "raw_response": result,
        }
