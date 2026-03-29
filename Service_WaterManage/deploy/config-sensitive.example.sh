# ==========================================
# 敏感信息配置文件
# ⚠️  此文件包含敏感信息，请勿提交到 Git！
# ==========================================
#
# 使用方法：
# 1. 复制 config.sh.example 为 config.sh
# 2. 填写实际的敏感信息
# 3. 确保 config.sh 已添加到 .gitignore
# ==========================================

# ==========================================
# 服务器认证配置（二选一）
# ==========================================

# 方式1: SSH 密钥（推荐）
SSH_KEY_PATH="$HOME/.ssh/jhw-ai-server.pem"
SERVER_PASSWORD=""

# 方式2: SSH 密码（不推荐，安全性较低）
# SSH_KEY_PATH=""
# SERVER_PASSWORD="your_password_here"

# ==========================================
# 阿里云配置（可选，用于自动配置安全组）
# ==========================================

# 如果需要自动配置安全组，请填写以下信息
# ALIYUN_ACCESS_KEY_ID="your_access_key_id"
# ALIYUN_ACCESS_KEY_SECRET="your_access_key_secret"
# ALIYUN_REGION_ID="cn-shenzhen"
# ALIYUN_INSTANCE_ID="your_instance_id"