# 图像识别OCR服务

简单易用的图像文字识别服务封装库。

## 主要功能

- 支持多种OCR服务提供商（百度OCR、阿里云OCR、华为云OCR等）
- 提供统一的OCR接口
- 支持百度OCR的令牌自动管理
- 支持令牌缓存和持久化存储

## 百度OCR令牌管理

BaiduTokenManager类提供完整的令牌管理功能：

- 自动获取访问令牌
- 检查令牌有效性
- 在令牌过期前自动刷新
- 优先使用刷新令牌
- 支持令牌持久化存储

## 使用示例

查看`baidu_token_example.py`文件了解百度令牌管理的使用方法。
查看`aliyun_ocr_example.py`文件了解阿里云OCR的使用方法。
查看`huawei_ocr_example.py`文件了解华为云OCR的使用方法。

## image-to-text

**Author:** purity3
**Version:** 0.0.1
**Type:** tool

### Description



