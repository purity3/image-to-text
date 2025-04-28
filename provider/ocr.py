from typing import Any, Dict, List, Type

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from lib.core.ocr_service import OCRService
from lib.providers import AliyunOCRProvider, HuaweiOCRProvider, BaiduOCRProvider
from lib.core.provider_base import OCRProvider


class OcrProvider(ToolProvider):
    # 定义提供商配置，包含参数映射、显示名称和提供商类
    PROVIDER_CONFIG = {
        "baidu": {
            "params": {
                "baidu_client_id": "client_id",
                "baidu_client_secret": "client_secret"
            },
            "display_name": "百度",
            "provider_class": BaiduOCRProvider
        },
        "huawei": {
            "params": {
                "huawei_ak": "access_key",
                "huawei_sk": "secret_key",
                "huawei_region": "region"
            },
            "display_name": "华为云",
            "provider_class": HuaweiOCRProvider
        },
        "aliyun": {
            "params": {
                "aliyun_access_key_id": "access_key_id",
                "aliyun_access_key_secret": "access_key_secret"
            },
            "display_name": "阿里云",
            "provider_class": AliyunOCRProvider
        }
    }

    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            # 获取默认提供商
            default_provider = credentials.get("default_provider", "baidu")
            
            # 检查默认提供商是否在配置中
            if default_provider not in self.PROVIDER_CONFIG:
                raise ValueError(
                    f"默认提供商 {default_provider} 无效，有效的提供商包括: {', '.join(self.PROVIDER_CONFIG.keys())}"
                )

            # 检查1: 默认提供商的参数不能为空
            default_config = self.PROVIDER_CONFIG[default_provider]
            default_required_params = list(default_config["params"].keys())
            
            for param in default_required_params:
                if not credentials.get(param):
                    raise ValueError(
                        f"默认提供商 {default_provider} 的参数 {param} 不能为空"
                    )

            # 检查2: 每组参数如果其中一个填写，其他也必须填写
            for provider, config in self.PROVIDER_CONFIG.items():
                params = list(config["params"].keys())
                has_any_param = any(credentials.get(param) for param in params)

                if has_any_param:
                    for param in params:
                        if not credentials.get(param):
                            raise ValueError(
                                f"提供商 {provider} 的参数 {param} 不能为空，因为其他相关参数已填写"
                            )

            # 检查3: 调用lib中的提供商验证方法验证参数格式和有效性
            self._validate_provider_credentials(credentials)

            print(f"凭据验证通过: {credentials}")
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
            
    def _validate_provider_credentials(self, credentials: dict[str, Any]) -> None:
        """
        使用lib中各提供商的authenticate方法验证参数
        
        Args:
            credentials: 用户提供的凭据
        
        Raises:
            ValueError: 如果参数无效
        """
        # 获取需要验证的提供商列表
        providers_to_check = self._get_providers_to_check(credentials)
        print(f"需要验证的提供商: {providers_to_check}")
        
        # 为每个提供商执行验证
        for provider in providers_to_check:
            config = self.PROVIDER_CONFIG[provider]
            try:
                # 检查参数完整性
                self._check_params_integrity(
                    credentials, 
                    list(config["params"].keys()), 
                    config["display_name"]
                )
                
                # 准备非None的参数
                provider_creds = self._prepare_provider_creds(credentials, config["params"])
                
                # 只有当所有必要参数都有非None值时才调用authenticate
                if len(provider_creds) == len(config["params"]):
                    config["provider_class"]().authenticate(**provider_creds)
                    
            except ValueError as e:
                # 重新抛出异常，添加提供商信息
                raise ValueError(f"{config['display_name']}提供商参数验证失败: {str(e)}")
                
    def _get_providers_to_check(self, credentials: dict[str, Any]) -> List[str]:
        """
        确定需要检查的提供商列表
        
        Args:
            credentials: 用户提供的凭据
            
        Returns:
            需要检查的提供商代码列表
        """
        providers_to_check = []
        
        for provider, config in self.PROVIDER_CONFIG.items():
            # 检查该提供商是否有任何非None参数
            if any(credentials.get(param) is not None for param in config["params"]):
                providers_to_check.append(provider)
                
        return providers_to_check
    
    def _prepare_provider_creds(self, credentials: dict[str, Any], param_map: Dict[str, str]) -> Dict[str, Any]:
        """
        根据参数映射准备提供商凭据
        
        Args:
            credentials: 用户提供的凭据
            param_map: 参数映射表
            
        Returns:
            提供商凭据字典
        """
        provider_creds = {}
        
        for source_key, target_key in param_map.items():
            if credentials.get(source_key) is not None:
                provider_creds[target_key] = credentials.get(source_key)
                
        return provider_creds
                
    def _check_params_integrity(self, credentials: dict[str, Any], params: list[str], provider_name: str) -> None:
        """
        检查参数完整性，确保一组参数要么全部提供，要么全部不提供
        
        Args:
            credentials: 用户提供的凭据
            params: 需要检查的参数列表
            provider_name: 提供商名称（用于错误消息）
            
        Raises:
            ValueError: 如果参数不完整
        """
        # 检查是否至少有一个参数被提供且不为None
        has_any_param = any(credentials.get(param) is not None for param in params)
        
        # 如果有参数被提供，则检查所有参数是否都被提供且不为None
        if has_any_param:
            for param in params:
                if credentials.get(param) is None:
                    raise ValueError(f"{provider_name}的参数 {param} 不能为空，因为其他相关参数已填写")
