[根目录](../CLAUDE.md) > **server**

# Server 模块文档

## 模块职责
Server 模块是 MTGScan App 的核心后端组件，负责：
- Web 服务器托管和请求处理
- 实时 WebSocket 通信
- 异步任务队列处理
- 图像 OCR 识别和卡牌分析
- 云存储文件上传管理

## 入口与启动

### 主应用文件: `app.py`
- Flask Web 应用初始化
- Socket.IO 实时通信配置
- Celery 任务队列配置
- 全局路由和事件处理

### 启动方式
```bash
# 开发模式
poetry run python app.py

# 生产模式 (Gunicorn + Eventlet)
poetry run gunicorn -w 8 -k eventlet --timeout 120 -b 0.0.0.0:5002 app:app

# Celery Worker
poetry run celery -A app.celery worker -P eventlet --loglevel=info
```

## 对外接口

### WebSocket 接口
- `scan` 事件: 接收图像数据进行识别
- `scan_result` 事件: 返回识别结果和标注图像
- `scan_text_only` 事件: 接收图像数据进行识别（仅返回文本结果）
- `scan_text_result` 事件: 返回纯文本识别结果

### REST API 接口
- `GET /api/<url>`: 通过 URL 识别图像中的卡牌
- `GET /api/text_only/<url>`: 通过 URL 识别图像中的卡牌（仅返回文本结果）
- `POST /api/fuzzy_search`: 模糊搜索卡牌名称

### 主要路由
- `GET /`: 主页面渲染
- `GET /api/text_only/<path:url>`: 仅返回卡牌文本结果的API接口

## 关键依赖与配置

### Python 依赖 (pyproject.toml)
```toml
mtgscan = {git = "https://github.com/Top-Decks/MTGSCAN"}
eventlet = "^0.36.1"
celery = "^5.2.0"
Flask = "^2.3.3"
Flask-SocketIO = "^5.3.6"
redis = "^4.3.4"
cos-python-sdk-v5 = "^1.9.36"
```

### 环境配置
- `REDIS_URL`: Redis 连接地址
- `AZURE_VISION_KEY`: Azure 计算机视觉密钥
- `AZURE_VISION_ENDPOINT`: Azure 计算机视觉端点
- `COS_SECRET_ID`: 腾讯云 COS Secret ID
- `COS_SECRET_KEY`: 腾讯云 COS Secret Key

## 数据模型

### 卡牌识别核心类
- `MagicRecognition`: 卡牌识别主类
- `Azure`: Azure OCR 服务封装
- `ScanTask`: Celery 任务基类

### 数据文件
- `data/all_cards.txt`: 完整的卡牌名称数据库
- `data/Keywords.json`: 万智牌关键词和能力数据

## 测试与质量

### 当前状态
- ❌ 单元测试: 缺失
- ❌ 集成测试: 缺失  
- ❌ 端到端测试: 缺失

### 质量工具建议
- `pytest`: Python 测试框架
- `pytest-cov`: 测试覆盖率检查
- `black`: 代码格式化
- `flake8`: 代码风格检查

## 常见问题 (FAQ)

### Q: 如何处理大文件上传？
A: 当前通过 Base64 编码在 WebSocket 中传输，建议改为分块上传或使用预签名 URL。

### Q: 如何扩展支持更多 OCR 服务？
A: 实现 OCR 服务接口抽象，支持多提供商切换。

### Q: 卡牌识别准确率如何优化？
A: 调整 `max_ratio_diff` 参数，优化卡牌数据库，添加图像预处理。

### Q: 如何只获取卡牌文本结果而不需要图片？
A: 使用新增的 `scan_text_only` WebSocket 事件或 `/api/text_only/<url>` HTTP 接口。

## 相关文件清单

- `app.py` - 主应用文件
- `pyproject.toml` - 依赖配置
- `poetry.lock` - 依赖锁文件
- `Dockerfile` - 容器构建配置
- `start.sh` - 启动脚本
- `utils/txoss.py` - 腾讯云 COS 工具
- `utils/oss.py` - OSS 工具（已弃用）
- `utils/apiclient.py` - API 客户端
- `data/all_cards.txt` - 卡牌数据库
- `data/Keywords.json` - 关键词数据
- `static/index.js` - 前端 JavaScript
- `static/style.css` - 样式文件
- `templates/index.html` - 主页面模板

## 变更记录 (Changelog)

### 2025-08-23 - 模块文档创建
- 创建 server 模块 CLAUDE.md 文档
- 记录模块结构、接口和依赖信息
- 标识测试缺口和质量改进建议

### 2025-08-23 - 新增纯文本接口
- 新增 `scan_text_only` WebSocket 事件处理
- 新增 `/api/text_only/<url>` HTTP 路由
- 两个接口均只返回卡牌识别文本结果，不包含图片

### 近期变更
- 替换 qcloud-cos 为 cos-python-sdk-v5
- 添加腾讯云 COS 支持
- 更新卡牌数据库文件