#!/bin/bash
# ============================================
# 生产环境密钥生成脚本
# ============================================
# 用途：生成生产环境所需的安全密钥
# 执行：本地执行
# ============================================

set -e

echo "========================================"
echo "  生产环境密钥生成工具"
echo "========================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    exit 1
fi

echo "正在生成生产环境密钥..."
echo ""

# 生成SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
echo "SECRET_KEY (用于应用加密):"
echo "$SECRET_KEY"
echo ""

# 生成JWT_SECRET_KEY
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
echo "JWT_SECRET_KEY (用于JWT令牌):"
echo "$JWT_SECRET_KEY"
echo ""

# 生成管理员密码建议
ADMIN_PASSWORD=$(python3 -c "import secrets, string; chars = string.ascii_letters + string.digits + '!@#$%^&*'; print(''.join(secrets.choice(chars) for _ in range(16)))")
echo "建议的管理员密码:"
echo "$ADMIN_PASSWORD"
echo ""

echo "========================================"
echo "  ⚠️  重要提醒"
echo "========================================"
echo ""
echo "1. 请妥善保管以上密钥，不要泄露"
echo "2. 将密钥添加到 .env 文件中:"
echo "   SECRET_KEY=$SECRET_KEY"
echo "   JWT_SECRET_KEY=$JWT_SECRET_KEY"
echo ""
echo "3. 部署后立即修改管理员密码为:"
echo "   $ADMIN_PASSWORD"
echo ""
echo "4. 建议将密钥保存到密码管理器中"
echo ""