# 历史部署脚本归档

此目录包含开发过程中创建的历史部署脚本，已被更优化的脚本替代。

## 📋 当前有效脚本

**请使用根目录下的以下脚本：**

| 脚本 | 用途 |
|------|------|
| `start_full_deploy.sh` | 首次完整部署 |
| `update.sh` | 增量更新（保护数据）|
| `start_all.sh` | 本地启动所有服务 |
| `stop_all.sh` | 停止所有服务 |

---

## 📦 归档脚本列表

此目录下的脚本已废弃，仅作参考：

- `auto_deploy_centos.sh` - CentOS自动部署（已废弃）
- `auto_deploy_from_local.sh` - 本地自动部署（已废弃）
- `deploy-production.sh` - 生产部署（已废弃）
- `deploy_alinux.sh` - Alibaba Cloud Linux部署（已废弃）
- `deploy_all_in_one.sh` - 一体化部署（已废弃）
- `deploy_centos.sh` - CentOS部署（已废弃）
- `deploy_centos_final.sh` - CentOS最终版（已废弃）
- `deploy_final_v2.sh` - 最终版v2（已废弃）
- `deploy_smart_v3.sh` - 智能版v3（已废弃）
- `final_deploy.sh` - 最终部署（已废弃）
- `go_deploy.sh` - 快速部署（已废弃）
- `run.sh` - 运行脚本（已废弃）
- `run_deploy.sh` - 运行部署（已废弃）
- `start_deploy.sh` - 启动部署（已废弃）

---

## ⚠️ 警告

**不要使用此目录下的脚本！**

这些脚本可能：
- 包含硬编码的密码
- 使用过时的部署方式
- 缺少数据保护机制
- 与当前系统不兼容

---

**归档时间**: 2026-04-04  
**归档原因**: 统一部署流程，使用更优化的脚本