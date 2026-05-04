# AI 小说家

全自动 AI 小说创作系统。从一个灵感出发，自动完成大纲规划、角色设定、世界观构建、章节创作、多层质检、分层记忆管理，直到完整小说的生成。

## 核心特性

### 创作流水线
- **大纲引擎** - 自动生成三幕式大纲、角色关系图、世界观圣经
- **章节创作** - 基于大纲逐章生成，支持流式输出
- **定向改写** - 质检不通过时精准定位问题段落重写，非全文重来

### 质量门禁（并行执行）
- **L1/L2/L3 一致性检查** - 时间线、空间、道具、人称自洽
- **原创性检测** - N-gram 重叠、模板相似度、词汇多样性
- **大纲对齐** - 检验章节与大纲规划的偏离度
- **情感曲线分析** - 紧张/放松/悲伤/愉悦四维度追踪

### 记忆系统
- **热记忆** - 最近 N 章完整内容，保持叙事连贯
- **温记忆** - 中期章节摘要，提取关键事件
- **冷记忆** - 角色状态、伏笔追踪、世界观规则

### 前端界面
- 暖色纸张风格 UI，Noto Serif SC 衬线字体
- 书房阅读模式，支持章节导航
- 质量雷达图、情感曲线、角色关系图谱可视化
- 深色/浅色主题切换
- 移动端响应式

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | FastAPI + SQLAlchemy + aiosqlite |
| 前端 | React 18 + TypeScript + Vite |
| LLM | OpenAI 兼容 API（默认 DeepSeek） |
| 存储 | SQLite |
| 可视化 | Chart.js + SVG |

## 快速开始

### 1. 环境要求
- Python 3.11+
- Node.js 18+
- OpenAI 兼容 API Key

### 2. 配置
```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 3. 启动
```bash
# Windows
启动.bat

# 或手动启动
# 后端
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 前端
cd frontend
npm install
npm run dev -- --port 3000
```

### 4. 访问
- 前端: http://localhost:3000
- API: http://localhost:8000/api
- 健康检查: http://localhost:8000/api/health

## 项目结构

```
ai-novelist/
├── backend/
│   ├── api/              # REST 路由 (stories, chapters, settings)
│   ├── core/             # 配置、模型、编排器、LLM 客户端
│   ├── generation/       # 大纲引擎、章节写作、提示词模板
│   ├── memory/           # 分层记忆、上下文构建、数据库
│   ├── quality/          # 一致性/原创性/对齐/情感曲线检查
│   ├── management/       # 伏笔管理、改写引擎、风格量化
│   └── pipeline/         # 并行质检流水线
├── frontend/
│   └── src/
│       ├── pages/        # 小说集、创作、书房、设定
│       ├── components/   # Button, Card, ErrorBoundary...
│       ├── hooks/        # useApi
│       ├── services/     # API + SSE 客户端
│       └── styles.ts     # 设计系统
├── prompts/              # 提示词模板（规划中）
└── .env.example          # 配置模板
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stories` | 获取所有小说 |
| POST | `/api/stories` | 创建新小说 |
| GET | `/api/stories/{id}` | 获取小说详情 |
| POST | `/api/stories/{id}/chapters` | 生成下一章 |
| GET | `/api/stories/{id}/chapters/{num}/stream` | SSE 流式生成 |
| GET | `/api/settings` | 获取配置 |
| PUT | `/api/settings` | 更新配置 |

## 配置说明

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `NOVELIST_LLM_API_KEY` | - | API Key |
| `NOVELIST_LLM_MODEL` | gpt-4o | 主模型 |
| `NOVELIST_LLM_FAST_MODEL` | gpt-4o-mini | 轻量模型 |
| `NOVELIST_LLM_TEMPERATURE` | 0.85 | 创作温度 |
| `NOVELIST_MAX_CONTEXT_TOKENS` | 64000 | 最大上下文 |
| `NOVELIST_MAX_REWRITE_ROUNDS` | 3 | 最大改写轮数 |

## License

MIT
