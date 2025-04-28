from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

# 导入OCR模块，确保提供商被自动注册
from lib import recognize_text

class AliyunOcrTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        调用阿里云OCR服务识别图片中的文字
        
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
            access_key_id = credentials.get("aliyun_access_key_id")
            access_key_secret = credentials.get("aliyun_access_key_secret")
            
            if not access_key_id or not access_key_secret:
                raise ValueError("阿里云OCR认证需要提供access_key_id和access_key_secret")
            
            # 准备认证凭据
            auth_credentials = {
                "access_key_id": access_key_id,
                "access_key_secret": access_key_secret
            }
            
            print(f"开始调用阿里云OCR，参数: url={url}")
            
            # 调用库函数识别文字
            result = recognize_text(
                url=url,
                provider="aliyun",
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
                    "provider": "阿里云OCR"
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
                    "provider": "阿里云OCR",
                    "raw_response": result.get("raw_response")
                })
        
        except Exception as e:
            # 处理异常
            error_message = f"OCR处理异常: {str(e)}"
            yield self.create_text_message(error_message)
            yield self.create_json_message({
                "success": False,
                "error": str(e),
                "provider": "阿里云OCR"
            }) 