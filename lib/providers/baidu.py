"""
百度OCR提供商实现
"""

import requests
import base64
import json
import time
import os
import functools
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from ..core.provider_base import OCRProvider


class BaiduOCRProvider(OCRProvider):
    """百度OCR服务提供商的具体实现，包含token管理功能"""

    # 用于本地存储的默认文件名
    DEFAULT_TOKEN_FILENAME = "baidu_ocr_token.json"
    # 默认存储到项目根目录的@cache文件夹
    DEFAULT_TOKEN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cache")

    def __init__(self, token_path: Optional[str] = None):
        # OCR服务认证相关
        self._access_token = None
        self._client_id = None
        self._client_secret = None

        # Token管理相关
        self._refresh_token = None
        self._expires_at = 0  # 过期时间戳
        self._scope = ""  # 权限范围

        # 本地文件存储路径
        self._token_path = token_path

    @property
    def provider_name(self) -> str:
        return "baidu"

    @functools.cache
    def get_token_file_path(self) -> str:
        """获取token文件存储路径，使用缓存避免重复计算"""
        if self._token_path:
            return self._token_path
            
        # 使用默认路径
        token_dir = self.DEFAULT_TOKEN_DIR
        # 确保目录存在
        os.makedirs(token_dir, exist_ok=True)
        # 使用固定文件名，不再包含client_id
        token_file = self.DEFAULT_TOKEN_FILENAME
        return os.path.join(token_dir, token_file)

    def validate_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证百度OCR认证凭据是否有效
        
        Args:
            credentials: 原始认证凭据，必须包含
                - client_id: API Key，用于获取访问令牌
                - client_secret: Secret Key，用于获取访问令牌
                可选包含
                - token_path: 自定义token存储路径
            
        Returns:
            处理后的凭据，用于authenticate方法
            
        Raises:
            ValueError: 如果凭据无效或不完整
        """
        # 检查必要的client_id和client_secret
        if not credentials.get("client_id") or not credentials.get("client_secret"):
            raise ValueError("百度OCR认证需要提供client_id和client_secret")
        
        # 返回所有认证相关参数
        result = {
            "client_id": credentials["client_id"],
            "client_secret": credentials["client_secret"]
        }
        
        # 添加可选的token存储路径
        if "token_path" in credentials:
            result["token_path"] = credentials["token_path"]
            
        return result

    def authenticate(self, **credentials) -> None:
        """
        获取百度AI平台的access_token

        Args:
            credentials: 认证凭据，必须包含client_id和client_secret，可选包含token_path
        """            
        # 必须提供client_id和client_secret
        if "client_id" not in credentials or "client_secret" not in credentials:
            raise ValueError("认证需要提供client_id和client_secret")

        self._client_id = credentials["client_id"]
        self._client_secret = credentials["client_secret"]
        
        # 设置自定义token存储路径（如果提供）
        if "token_path" in credentials:
            self._token_path = credentials["token_path"]
            # 如果更改了token路径，需要清除缓存
            self.get_token_file_path.cache_clear()
        
        # 尝试加载token信息
        self._load_token()
        
        # 获取访问令牌，如果本地没有有效的token，将自动获取新token
        token, _ = self.get_token()
        self._access_token = token
        
        if not self._access_token:
            raise Exception("获取access_token失败")

    def is_authenticated(self) -> bool:
        return self._access_token is not None

    def recognize_text(
        self, image_data: Optional[bytes], options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用百度OCR识别图片中的文字(仅支持URL方式)

        Args:
            image_data: 图片的二进制数据，现在总是为None，保留此参数是为了向后兼容
            options: 必须包含:
                - url: 图片URL地址
                可选包含:
                - language_type: 语言类型，如"CHN_ENG"（中英文混合）、"ENG"（英文）等

        Returns:
            识别结果字典
            
        Raises:
            ValueError: 如果options中不包含url
        """
        # 确保有有效的访问令牌
        token, refreshed = self.get_token()
        if refreshed or not self._access_token:
            self._access_token = token

        if not self.is_authenticated():
            raise Exception("未认证，请先调用authenticate方法")

        # 确保options中包含url
        if not options or "url" not in options:
            raise ValueError("options必须包含url参数")

        url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={self._access_token}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        # 准备请求数据，使用URL模式
        data = {"url": options["url"]}

        # 添加可选参数
        if "language_type" in options:
            data["language_type"] = options["language_type"]
            
        # 添加其他可选参数，排除url
        for key, value in options.items():
            if key not in ["url", "language_type"] and key not in data:
                data[key] = value

        try:
            print(f"调用百度OCR API，使用URL: {options['url']}")
            response = requests.post(url, data=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # 如果是401/403错误，可能是令牌过期，尝试刷新
            if hasattr(e, 'response') and e.response and e.response.status_code in (401, 403):
                token, refreshed = self.get_token(force_refresh=True)
                if refreshed:
                    self._access_token = token
                    # 使用新令牌重试请求
                    return self.recognize_text(None, options)
            raise Exception(f"OCR识别失败: {str(e)}")

    # --- 以下是Token管理相关方法 ---

    @functools.cache
    def _load_token(self) -> None:
        """从本地文件加载令牌信息，使用缓存提高性能"""
        token_file_path = self.get_token_file_path()
        
        try:
            if os.path.exists(token_file_path):
                with open(token_file_path, 'r', encoding='utf-8') as f:
                    token_data = json.load(f)
                    self._access_token = token_data.get("access_token")
                    self._refresh_token = token_data.get("refresh_token")
                    self._expires_at = token_data.get("expires_at", 0)
                    self._scope = token_data.get("scope", "")
                print(f"已从本地文件加载token: {token_file_path}")
            else:
                print(f"未找到token文件: {token_file_path}，将获取新token")
                self._access_token = None
                self._refresh_token = None
                self._expires_at = 0
                self._scope = ""
        except Exception as e:
            print(f"从本地文件加载令牌失败: {e}")
            # 出现异常时，清空token信息以确保能够获取新token
            self._access_token = None
            self._refresh_token = None
            self._expires_at = 0
            self._scope = ""

    def _save_token(self) -> None:
        """将令牌信息保存到本地文件"""
        # 只有当访问令牌存在时才保存
        if not self._access_token:
            print("访问令牌为空，不保存token信息")
            return

        token_data = {
            "access_token": self._access_token,
            "refresh_token": self._refresh_token,
            "expires_at": self._expires_at,
            "scope": self._scope,
        }

        try:
            token_file_path = self.get_token_file_path()
            # 确保目录存在
            os.makedirs(os.path.dirname(token_file_path), exist_ok=True)
            
            with open(token_file_path, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, ensure_ascii=False, indent=2)
            
            print(f"成功保存token到本地文件: {token_file_path}")
            print(f"过期时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self._expires_at))}")
            
            # 更新加载token的缓存
            self._load_token.cache_clear()
        except Exception as e:
            print(f"保存令牌到本地文件失败: {e}")

    @functools.cache
    def get_token(self, force_refresh: bool = False) -> Tuple[str, bool]:
        """
        获取有效的访问令牌，如果过期或即将过期则刷新
        使用缓存提高性能，减少重复获取

        Args:
            force_refresh: 是否强制刷新令牌，不考虑过期时间

        Returns:
            (access_token, is_refreshed): 访问令牌和是否刷新的标志
        """
        # 强制刷新会清除缓存
        if force_refresh:
            self.get_token.cache_clear()
            
        # 检查是否需要获取或刷新令牌
        if force_refresh or not self.is_token_valid():
            refreshed = self.refresh_token()
            return self._access_token, refreshed
        return self._access_token, False

    def is_token_valid(self, buffer_seconds: int = 300) -> bool:
        """
        检查访问令牌是否有效（未过期）

        Args:
            buffer_seconds: 提前视为过期的缓冲时间（秒），默认5分钟

        Returns:
            令牌是否有效
        """
        # 没有令牌或过期时间，视为无效
        if not self._access_token or not self._expires_at:
            return False

        # 当前时间 + 缓冲时间 < 过期时间，则视为有效
        return (time.time() + buffer_seconds) < self._expires_at

    def fetch_new_token(self) -> Dict[str, Any]:
        """
        从百度获取新的令牌

        Returns:
            包含令牌信息的字典
        """
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"获取新令牌失败: {e}")

    def refresh_with_refresh_token(self) -> Dict[str, Any]:
        """
        使用刷新令牌获取新的访问令牌

        Returns:
            包含新令牌信息的字典
        """
        if not self._refresh_token:
            raise ValueError("没有可用的刷新令牌")

        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "refresh_token", "refresh_token": self._refresh_token}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"使用刷新令牌刷新失败: {e}")

    def refresh_token(self) -> bool:
        """
        刷新访问令牌，优先使用刷新令牌，失败则获取新令牌

        Returns:
            是否成功刷新
        """
        try:
            # 首先尝试使用刷新令牌
            if self._refresh_token:
                try:
                    result = self.refresh_with_refresh_token()
                    self._update_token_info(result)
                    # 刷新成功，清除相关缓存
                    self.get_token.cache_clear()
                    return True
                except Exception:
                    # 刷新令牌失败，尝试获取新令牌
                    pass

            # 获取全新的令牌
            result = self.fetch_new_token()
            self._update_token_info(result)
            # 刷新成功，清除相关缓存
            self.get_token.cache_clear()
            return True

        except Exception as e:
            print(f"刷新令牌失败: {e}")
            return False

    def _update_token_info(self, token_data: Dict[str, Any]) -> None:
        """
        更新令牌信息

        Args:
            token_data: 包含令牌信息的字典
        """
        self._access_token = token_data.get("access_token")
        self._refresh_token = token_data.get("refresh_token", self._refresh_token)
        self._scope = token_data.get("scope", self._scope)

        # 计算过期时间（当前时间 + expires_in）
        expires_in = token_data.get("expires_in", 0)
        if expires_in:
            self._expires_at = time.time() + expires_in

        # 保存令牌信息
        self._save_token()

    def get_token_info(self) -> Dict[str, Any]:
        """
        获取当前的令牌信息

        Returns:
            包含令牌信息的字典
        """
        expires_in = int(self._expires_at - time.time()) if self._expires_at else 0

        return {
            "access_token": self._access_token,
            "refresh_token": self._refresh_token,
            "expires_in": expires_in if expires_in > 0 else 0,
            "scope": self._scope,
        }

    def format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        将百度OCR原始识别结果格式化为统一格式
        
        Args:
            result: 原始识别结果
            
        Returns:
            统一格式的结果: {"text": "识别的文本内容", "provider": "百度", "raw_response": 原始响应}
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
                    "error_msg": error_msg or "百度OCR服务返回错误",
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
