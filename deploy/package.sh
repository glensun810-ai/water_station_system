#!/bin/bash
# 打包部署文件

tar -czf ../jhw-ai-deploy.tar.gz \
  --exclude='deploy/package.sh' \
  deploy/

echo "✓ 部署包已创建: ../jhw-ai-deploy.tar.gz"
echo "  大小: $(ls -lh ../jhw-ai-deploy.tar.gz | awk '{print $5}')"
