<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/ZhaoDezhang9/ai-novelist/main/.github/logo-dark.svg">
    <img alt="AI 小说家" src="https://raw.githubusercontent.com/ZhaoDezhang9/ai-novelist/main/.github/logo-light.svg" width="480">
  </picture>
</p>

<p align="center">
  <strong>一句话灵感，换一本完整小说。</strong>
</p>

<p align="center">
  <a href="https://github.com/ZhaoDezhang9/ai-novelist/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/tech-FastAPI_%2B_React-green" alt="Stack"></a>
  <a href="#"><img src="https://img.shields.io/badge/model-OpenAI_Compatible-orange" alt="Models"></a>
  <a href="#"><img src="https://img.shields.io/badge/language-中文_%7C_English-red" alt="Language"></a>
</p>

---

## 为什么选择 AI 小说家

市面上有太多"AI 写小说"的产品，你把灵感扔进去，它吐出一段还不错的文字——然后呢？没有大纲，角色会突变，第三章就忘了第一章埋的伏笔，结尾纯粹是胡扯。

**AI 小说家解决的是整本书创作的问题。**

```
你的一句灵感
    ↓
大纲 + 世界观 + 角色档案（自动生成）
    ↓
第1章 → 质检 → 改写 → 通过
第2章 → 质检 → 改写 → 通过
  ⋮
第N章 → 质检 → 通过
    ↓
完整的书
```

### 与其他 AI 写作工具对比

| | AI 小说家 | 在线 AI 写作工具 |
|---|---|---|
| 代码 | 开源，可修改 | 闭源，不可见 |
| 数据 | 完全本地，你的内容你做主 | 传输到对方服务器 |
| 模型 | OpenAI 兼容 API，可接任何模型 | 绑死官方模型 |
| 创作流程 | 大纲→章节→质检→改写，完整闭环 | 只能单次生成 |
| 长篇记忆 | 热/温/冷三层记忆 | 靠 prompt 硬塞，超出窗口就忘 |
| 可视化 | 雷达图/情绪曲线/角色图谱 | 无 |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env → 把 NOVELIST_LLM_API_KEY 换成你自己的 Key

# 3. 启动
./启动.bat                          # Windows
# 或:
uvicorn backend.main:app --reload --port 8000
cd frontend && npm run dev          # 另一个终端
```

打开浏览器，访问 **http://localhost:3000**，写下一句灵感开始创作。

### Docker

```bash
docker compose up -d
# 后端 :8000, 前端 :3000
```

## 核心特性

**大纲生成** — 从灵感自动生成完整三幕结构大纲、世界观、角色档案

**章节创作** — 流式输出，上下文感知，风格一致。支持全本自动续写，断点恢复

**四维质量门禁** — 每章完成后并行质检：
- 一致性检查：人物设定、世界观、时间线
- 原创性检测：模板化套路检测 + 词汇多样性分析
- 大纲对齐度：确保章节不偏离故事主线
- 情绪节奏分析：紧张/放松/悲伤/愉悦四维追踪

**三层记忆系统** — 热记忆（最近2章全文）+ 温记忆（最近5章摘要）+ 冷记忆（长期伏笔追踪）

**精确改写** — 质检失败时只改问题段落，400字窗口，最多3轮

**五维阅读体验**
- 阅读模式：衬线体 + 打字机效果
- 六维质量雷达图
- 情绪曲线 SVG 图表
- 角色关系力导向图
- 三幕结构大纲追踪

**已实现的功能**
- 暗色/暖色主题切换，CSS 变量驱动，所有组件自动跟随
- 路由级代码分割，首屏 18KB
- TXT / HTML / EPUB 导出
- 故事搜索、流派/状态筛选、排序
- Toast 通知 + ConfirmDialog，非阻塞式交互反馈
- 移动端适配（抽屉式侧边栏、折叠章节列表）
- SSE 流式创作进度实时展示

## 技术架构

```
User → Frontend (React + TypeScript + Vite)
         ↓ HTTP + SSE
      Backend (FastAPI)
         ↓
    NovelOrchestrator
    ├── OutlineEngine       # 大纲 + 世界观 + 角色
    ├── ChapterWriter       # 章节生成 + 流式输出
    ├── TieredMemory        # 热/温/冷记忆
    ├── QualityGates        # 并行四维质检
    │   ├── ConsistencyChecker
    │   ├── OriginalityChecker
    │   ├── AlignmentChecker
    │   └── EmotionalCurveAnalyzer
    └── RewriteEngine       # 定向改写
```

### 技术栈

**后端**
<p>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.136-009688?style=flat-square&logo=fastapi" alt="FastAPI"></a>
  <a href="https://docs.pydantic.dev"><img src="https://img.shields.io/badge/Pydantic-2.13-E92063?style=flat-square&logo=pydantic" alt="Pydantic"></a>
  <a href="https://www.sqlalchemy.org"><img src="https://img.shields.io/badge/SQLAlchemy-2.0-1C1C1C?style=flat-square" alt="SQLAlchemy"></a>
  <a href="https://docs.python.org/3/"><img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python" alt="Python"></a>
</p>

**前端**
<p>
  <a href="https://react.dev"><img src="https://img.shields.io/badge/React-19.2-61DAFB?style=flat-square&logo=react" alt="React"></a>
  <a href="https://www.typescriptlang.org"><img src="https://img.shields.io/badge/TypeScript-6.0-3178C6?style=flat-square&logo=typescript" alt="TypeScript"></a>
  <a href="https://vitejs.dev"><img src="https://img.shields.io/badge/Vite-8.0-646CFF?style=flat-square&logo=vite" alt="Vite"></a>
  <a href="https://reactrouter.com"><img src="https://img.shields.io/badge/React_Router-7.15-CA4245?style=flat-square&logo=react-router" alt="React Router"></a>
</p>

**数据存储**
<p>
  <a href="https://sqlite.org"><img src="https://img.shields.io/badge/SQLite-3.45+-003B57?style=flat-square&logo=sqlite" alt="SQLite"></a>
  <a href="https://aiosqlite.omnilib.dev"><img src="https://img.shields.io/badge/aiosqlite-0.22-008080?style=flat-square" alt="aiosqlite"></a>
</p>

## 配置

复制 `.env.example` 为 `.env` 并配置关键项：

```bash
# LLM
NOVELIST_LLM_API_KEY=sk-your-key-here
NOVELIST_LLM_API_BASE=https://api.openai.com/v1
NOVELIST_LLM_MODEL=gpt-4o
NOVELIST_LLM_FAST_MODEL=gpt-4o-mini

# 记忆系统
NOVELIST_HOT_CHAPTERS=2
NOVELIST_WARM_SUMMARY_CHAPTERS=5
NOVELIST_MAX_CONTEXT_TOKENS=64000

# 质量门禁阈值
NOVELIST_NGRAM_OVERLAP_THRESHOLD=0.15
NOVELIST_TEMPLATE_SIMILARITY_THRESHOLD=0.7
NOVELIST_VOCAB_DIVERSITY_THRESHOLD=0.4
NOVELIST_TWIST_DENSITY_MIN=0.00033
NOVELIST_ALIGNMENT_SCORE_MIN=0.75
```

完整的配置项见 `.env.example`。

## 路线图

- 多 LLM 提供商一键切换（DeepSeek / OpenAI / 本地模型 Ollama）
- 用户系统：多用户各自私密故事库
- 协作创作：用户提供方向，AI 生成多个分支供选择
- AI 插画生成：章节配图自动生成
- 语音朗读：AI 语音朗读生成章节
- 剧本模式：小说转剧本格式

## 贡献

欢迎贡献！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

```bash
git clone https://github.com/ZhaoDezhang9/ai-novelist.git
cd ai-novelist
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 运行开发服务器
uvicorn backend.main:app --reload --port 8000
cd frontend && npm run dev          # 另一个终端
```

## 许可证

MIT License — 可随意使用、修改、分发，包括商业用途。

## 生态兼容

- 支持所有 OpenAI 兼容 API：DeepSeek、Qwen、GLM、OpenAI 等
- 支持 Docker 部署
- 中文优先，英文完整支持

---

<p align="center">
  <sub>Built by <a href="https://github.com/ZhaoDezhang9">ZhaoDezhang9</a></sub>
</p>
