# AI产业集群空间服务系统 - 快捷启动器

## 📁 文件清单

启动器包含以下文件：

| 文件名 | 说明 | 适用平台 |
|--------|------|---------|
| `start_services.py` | Python启动脚本（主程序） | Windows/Mac/Linux ✅ |
| `start_services.bat` | Windows批处理启动脚本 | Windows ✅ |
| `start_services.sh` | Linux/Mac Shell启动脚本 | Linux/Mac ✅ |
| `start_services_example.py` | 使用示例代码 | Windows/Mac/Linux ✅ |
| `快速启动指南.md` | 详细使用文档 | - ✅ |
| `启动程序说明.md` | 本文件 | - ✅ |

## 🚀 快速开始

### Windows用户
双击 `start_services.bat` 即可

### Mac/Linux用户
运行：
```bash
./start_services.sh
```

### 通用方法
```bash
python start_services.py
```

## ✨ 核心功能

### 1. 自动端口检测
- ✅ 自动扫描8000-8099端口
- ✅ 自动选择可用端口
- ✅ 避免端口冲突

### 2. 自动启动服务
- ✅ 依次启动水站、会议室、用餐三个服务
- ✅ 自动检查服务启动状态
- ✅ 显示启动进度

### 3. 自动打开浏览器
- ✅ 启动成功后自动打开系统首页
- ✅ 支持所有主流浏览器
- ✅ 可手动禁用（编辑脚本）

### 4. 统一日志管理
- ✅ 所有服务日志统一保存到logs目录
- ✅ 自动创建日志目录
- ✅ 实时写入日志

### 5. 一键停止
- ✅ Ctrl+C停止所有服务
- ✅ 优雅关闭，确保数据完整性
- ✅ 自动清理进程

## 🌐 访问地址

启动后会显示以下访问地址：

```
🏠 首页: http://localhost:8000/portal/index.html
💧 水站管理: http://localhost:8000/water-admin/index.html
🏢 会议室: http://localhost:8000/meeting-frontend/index.html
🍽️ 用餐管理: http://localhost:8000/portal/admin/dining.html
📊 API文档: http://localhost:8000/docs
```

## 📋 启动流程

```
1. 检查Python环境
   ↓
2. 检查端口占用
   ↓
3. 启动水站服务 (8000)
   ↓
4. 启动会议室服务 (8001)
   ↓
5. 启动用餐服务 (8002)
   ↓
6. 打开浏览器
   ↓
7. 显示访问地址
```

## 🔧 配置说明

### 默认端口分配

| 服务 | 默认端口 | 端口范围 | 说明 |
|------|---------|---------|------|
| 水站服务 | 8000 | 8000-8099 | 主服务，包含Portal |
| 会议室服务 | 8001 | 8000-8099 | 独立服务 |
| 用餐服务 | 8002 | 8000-8099 | 独立服务 |

### 日志文件路径

```
logs/
├── water_service.log       # 水站服务日志
├── meeting_service.log     # 会议室服务日志
└── dining_service.log      # 用餐服务日志
```

## 🐛 故障排查

### 端口被占用
**现象**: 提示端口被占用
**解决**: 启动器会自动选择其他端口，无需手动处理

### 服务启动失败
**现象**: 提示服务启动超时或失败
**解决**:
```bash
# 1. 查看日志文件
cat logs/water_service.log
cat logs/meeting_service.log
cat logs/dining_service.log

# 2. 检查Python版本
python --version  # 需要3.8+

# 3. 安装依赖
pip install -r requirements.txt
```

### 浏览器未打开
**现象**: 服务启动成功但浏览器未自动打开
**解决**: 手动在浏览器中访问显示的首页地址

### Python未安装
**现象**: 提示找不到Python
**解决**: 从 https://python.org 下载并安装Python 3.8+

## 💡 高级配置

### 修改默认端口
编辑 `start_services.py`：
```python
water_port = find_available_port(9000)  # 从9000开始
meeting_port = find_available_port(9001)
dining_port = find_available_port(9002)
```

### 禁用自动打开浏览器
编辑 `start_services.py`，注释掉：
```python
# webbrowser.open(primary_url)
```

### 修改服务配置
编辑各服务的配置文件：
- `Service_WaterManage/backend/config/settings.py`
- `Service_MeetingRoom/backend/config/settings.py`
- `Service_Dining/backend/config/settings.py`

## 📖 使用示例

查看 `start_services_example.py` 了解如何：
- 启动单个服务
- 检查端口占用
- 停止服务

```bash
python start_services_example.py
```

## 🔍 测试状态

✅ 端口检查功能 - 正常
✅ 端口查找功能 - 正常
✅ 项目路径识别 - 正常
✅ 服务启动功能 - 正常
✅ 浏览器打开功能 - 正常
✅ 日志记录功能 - 正常
✅ 一键停止功能 - 正常

## 📝 更新日志

### v1.0 (2026-04-06)
- ✅ 初始版本发布
- ✅ 自动端口检测
- ✅ 自动启动服务
- ✅ 自动打开浏览器
- ✅ 统一日志管理
- ✅ 一键停止所有服务
- ✅ 跨平台支持（Windows/Mac/Linux）

## 📞 技术支持

如有问题，请：
1. 查看日志文件：`logs/*.log`
2. 查看 `快速启动指南.md`
3. 查看 `云服务器部署配置说明.md`

## ⚠️ 注意事项

1. **首次运行**: 确保已安装Python 3.8+
2. **依赖安装**: 首次运行可能需要安装依赖
3. **端口冲突**: 启动器会自动处理，无需担心
4. **停止服务**: 使用Ctrl+C优雅停止，避免数据丢失
5. **生产环境**: 建议使用Gunicorn和Nginx部署

## 🎯 最佳实践

1. **开发环境**: 使用启动器快速启动和调试
2. **生产环境**: 使用systemd或supervisor管理服务
3. **日志监控**: 定期检查日志文件
4. **备份策略**: 定期备份数据库和配置文件

## 📄 相关文档

- `快速启动指南.md` - 详细使用指南
- `云服务器部署配置说明.md` - 生产环境部署
- `48-系统重构实施计划.md` - 系统架构说明
- `49-功能可用性检查报告.md` - 功能检查报告
- `50-水站管理和会议室预定API清单.md` - API文档

---

**版本**: v1.0
**更新日期**: 2026-04-06
**维护者**: AI产业集群空间服务系统团队