from collections.abc import Generator
from enum import Enum
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

# 导入OCR模块，确保提供商被自动注册
from lib import recognize_text

class LanguageType(Enum):
    """OCR识别支持的语言类型"""
    CHN_ENG = "CHN_ENG"  # 中英文混合
    ENG = "ENG"  # 英文
    POR = "POR"  # 葡萄牙语
    FRE = "FRE"  # 法语
    GER = "GER"  # 德语
    ITA = "ITA"  # 意大利语
    SPA = "SPA"  # 西班牙语
    RUS = "RUS"  # 俄语
    JAP = "JAP"  # 日语
    KOR = "KOR"  # 韩语

class BaiduOcrTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        调用百度OCR服务识别图片中的文字
        
        Args:
            tool_parameters: 包含以下参数:
                - url: 图片URL
                - language: 识别的语言类型，参考LanguageType枚举
                
        Returns:
            识别结果，包含JSON和文本格式
        """
        try:
            # 从参数中获取URL和语言类型
            url = tool_parameters.get("url")
            if not url:
                raise ValueError("必须提供图片URL")
                
            # 获取语言类型，默认为中英文混合
            language = tool_parameters.get("language", LanguageType.CHN_ENG.value)
            
            # 从凭据中获取认证信息
            credentials = self.runtime.credentials
            client_id = credentials.get("baidu_client_id")
            client_secret = credentials.get("baidu_client_secret")
            
            if not client_id or not client_secret:
                raise ValueError("百度OCR认证需要提供client_id和client_secret")
            
            # 准备认证凭据
            auth_credentials = {
                "client_id": client_id,
                "client_secret": client_secret
            }
            
            print(f"开始调用百度OCR，参数: url={url}, language={language}")
            
            # 调用库函数识别文字
            result = recognize_text(
                url=url,
                provider="baidu",
                lang=language,
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
                    "provider": "百度OCR"
                })
            else:
                # 识别成功
                text_content = result.get("text", "")
                
                # 返回文本结果
                if text_content:
                    yield self.create_text_message(f"识别结果:\n{text_content}")
                else:
                    yield self.create_text_message("图片中未识别到文字")
                
                # 返回JSON结果
                yield self.create_json_message({
                    "success": True,
                    "text": text_content,
                    "provider": "百度OCR",
                    "language": language,
                    "raw_response": result.get("raw_response")
                })
        
        except Exception as e:
            # 处理异常
            error_message = f"OCR处理异常: {str(e)}"
            yield self.create_text_message(error_message)
            yield self.create_json_message({
                "success": False,
                "error": str(e),
                "provider": "百度OCR"
            })
