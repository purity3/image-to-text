from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class OcrProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            # 获取默认提供商
            default_provider = credentials.get("default_provider", "baidu")
            
            # 定义每个提供商需要的参数
            provider_params = {
                "baidu": ["baidu_client_id", "baidu_client_secret"],
                "huawei": ["huawei_ak", "huawei_sk", "huawei_region"],
                "aliyun": ["aliyun_access_key_id", "aliyun_access_key_secret"]
            }
            
            # 检查1: 默认提供商的参数不能为空
            default_required_params = provider_params.get(default_provider, [])
            for param in default_required_params:
                if not credentials.get(param):
                    raise ValueError(f"默认提供商 {default_provider} 的参数 {param} 不能为空")
            
            # 检查2: 每组参数如果其中一个填写，其他也必须填写
            for provider, params in provider_params.items():
                # 检查是否有任何一个参数被填写
                has_any_param = any(credentials.get(param) for param in params)
                
                # 如果有任何一个参数被填写，则检查所有参数是否都被填写
                if has_any_param:
                    for param in params:
                        if not credentials.get(param):
                            raise ValueError(f"提供商 {provider} 的参数 {param} 不能为空，因为其他相关参数已填写")
            
            print(f"凭据验证通过: {credentials}")
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
