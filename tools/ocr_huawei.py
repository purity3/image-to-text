from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

# 导入OCR模块，确保提供商被自动注册
from lib import recognize_text

class HuaweiOcrTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        调用华为云OCR服务识别图片中的文字
        
        Args:
            tool_parameters: 包含以下参数:
                - url: 图片URL
                
        Returns:
            识别结果，包含JSON和文本格式
        """
        try:
            # 从参数中获取URL
            url = tool_parameters.get("url")
            if not url:
                raise ValueError("必须提供图片URL")
            
            # 从凭据中获取认证信息
            credentials = self.runtime.credentials
            access_key = credentials.get("huawei_ak")
            secret_key = credentials.get("huawei_sk")
            region = credentials.get("huawei_region","cn-north-4")
            
            if not access_key or not secret_key:
                raise ValueError("华为云OCR认证需要提供access_key和secret_key")
                
            if not region:
                raise ValueError("华为云OCR认证需要提供region")
            
            # 准备认证凭据
            auth_credentials = {
                "access_key": access_key,
                "secret_key": secret_key,
                "region": region
            }
            
            print(f"开始调用华为云OCR，参数: url={url}")
            
            # 调用库函数识别文字
            result = recognize_text(
                url=url,
                provider="huawei",
                credentials=auth_credentials
            )
            
            # 生成结果
            if result.get("error", False):
                # 识别失败
                error_message = f"OCR识别失败: {result.get('error_msg', '未知错误')}"
                yield self.create_text_message(error_message)
                yield self.create_json_message({
                    "success": False,
                    "error": result.get("error_msg", "未知错误"),
                    "provider": "huawei"
                })
            else:
                # 识别成功
                text_content = result.get("text", "")
                
                # 返回文本结果
                if text_content:
                    yield self.create_text_message(f"{text_content}")
                else:
                    yield self.create_text_message("图片中未识别到文字")
                
                # 返回JSON结果
                yield self.create_json_message({
                    "success": True,
                    "text": text_content,
                    "provider": "huawei",
                    "raw": result.get("raw_response", {})
                })
        
        except Exception as e:
            # 处理异常
            error_message = f"OCR处理异常: {str(e)}"
            yield self.create_text_message(error_message)
            yield self.create_json_message({
                "success": False,
                "error": str(e),
                "provider": "huawei"
            }) 