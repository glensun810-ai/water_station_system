"""
支付配置文件模板
请根据实际情况填写配置参数
"""

# 支付宝支付配置
ALIPAY_CONFIG = {
    # 应用ID（从支付宝开放平台获取）
    "app_id": "YOUR_APP_ID",  # 例如：2021001234567890
    # 应用私钥文件路径（需要生成RSA2密钥）
    "private_key_path": "/path/to/app_private_key.pem",
    # 支付宝公钥文件路径（从支付宝开放平台获取）
    "alipay_public_key_path": "/path/to/alipay_public_key.pem",
    # 是否使用沙箱环境（开发阶段建议使用True）
    "debug": True,  # 生产环境设为False
    # 异步通知URL（支付成功后支付宝会回调这个地址）
    "notify_url": "http://localhost:8000/api/payment/callback/alipay",
    # 同步返回URL（支付完成后跳转的页面）
    "return_url": "http://localhost:8000/portal/payment/result.html",
}

# 微信支付配置（待实现）
WECHATPAY_CONFIG = {
    # 应用ID
    "appid": "YOUR_WECHAT_APP_ID",
    # 商户ID
    "mch_id": "YOUR_MCH_ID",
    # API密钥
    "api_key": "YOUR_API_KEY",
    # 商户证书路径
    "cert_path": "/path/to/apiclient_cert.pem",
    # 商户私钥路径
    "key_path": "/path/to/apiclient_key.pem",
    # 异步通知URL
    "notify_url": "http://localhost:8000/api/payment/callback/wechat",
}

# 发票配置（待实现）
INVOICE_CONFIG = {
    # 电子发票平台API配置
    "api_url": "https://invoice-api.example.com",
    "api_key": "YOUR_INVOICE_API_KEY",
    # 发票PDF存储路径
    "storage_path": "/path/to/invoices",
    # 邮件发送配置
    "smtp_host": "smtp.example.com",
    "smtp_port": 587,
    "smtp_user": "your_email@example.com",
    "smtp_password": "YOUR_EMAIL_PASSWORD",
}

"""
配置步骤说明：

1. 支付宝配置：
   a. 登录支付宝开放平台：https://open.alipay.com
   b. 创建应用（选择"网页/移动应用"）
   c. 添加"电脑网站支付"能力
   d. 生成RSA2密钥对：
      - 使用支付宝提供的密钥生成工具
      - 或使用openssl命令：
        openssl genrsa -out app_private_key.pem 2048
        openssl rsa -in app_private_key.pem -pubout -out app_public_key.pem
   e. 上传应用公钥到支付宝平台
   f. 从支付宝平台下载支付宝公钥
   g. 将私钥和支付宝公钥文件放置到服务器
   h. 配置回调URL（需要在支付宝平台设置）

2. 沙箱环境测试：
   - 沙箱环境APP_ID和密钥可从：
     https://openhome.alipay.com/platform/appDaily.htm 获取
   - 使用沙箱买家账号进行支付测试
   - debug参数设为True

3. 生产环境：
   - 将debug参数设为False
   - 使用正式的APP_ID和密钥
   - 配置正式的回调URL（需要HTTPS）
   - 配置服务器IP白名单

4. 微信支付配置：
   - 登录微信支付商户平台
   - 获取商户ID和API密钥
   - 下载商户证书
   - 配置回调URL

注意事项：
- 私钥文件必须妥善保管，不要泄露
- 回调URL必须能被支付宝访问（不能是内网地址）
- 生产环境回调URL必须使用HTTPS
- 配置完成后需要重启服务
"""
