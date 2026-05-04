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

<br>

---

## ✨ 为什么选择 AI 小说家

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
第20章 → 质检 → 通过
    ↓
完整的书
```

### 🆚 与其他 AI 写作工具对比

| | AI 小说家 | 在线 AI 写作工具 |
|---|---|---|
| 代码 | 开源，可修改 | 闭源，不可见 |
| 数据 | 完全本地，你的内容你做主 | 传输到对方服务器 |
| 模型 | OpenAI 兼容 API，可接任何模型 | 绑死官方模型 |
| 创作流程 | 大纲→章节→质检→改写，完整闭环 | 只能单次生成 |
| 长篇记忆 | 热/温/冷三层记忆 | 靠 prompt 硬塞，超出窗口就忘 |
| 可视化 | 雷达图/情绪曲线/角色图谱 | 无 |

## 🚀 快速开始

```bash
# 1. 安装后端依赖
pip install -r requirements.txt

# 2. 安装前端依赖
cd frontend && npm install && cd ..

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env → 把 NOVELIST_LLM_API_KEY 换成你自己的 Key

# 4. 启动应用
./启动.bat  # Windows
# 或手动启动：
# uvicorn backend.main:app --reload --port 8000
# cd frontend && npm run dev
```

打开浏览器，访问 **http://localhost:3000**

在创作页写下一句灵感，点击"AI 生成标题和主题"，然后开始创作。

## 🎯 核心特性

### 📝 **智能大纲生成**
- 自动从灵感生成完整故事大纲
- 三幕结构规划，确保故事节奏
- 世界观构建与角色档案创建
- 章节拍点设计，每章都有明确目标

### ✍️ **章节创作引擎**
- 流式输出，实时观看创作过程
- 多模型支持（GPT-4o、DeepSeek、Qwen、GLM等）
- 上下文感知，保持前后文连贯
- 风格一致性，维持作者语调

### 🛡️ **四维质量门禁**
每章完成后自动进行四项并行质检：
- **一致性检查**：人物设定、世界观、时间线
- **原创性检测**：模板化套路检测 + 词汇多样性分析
- **大纲对齐度**：确保章节不偏离故事主线
- **情绪节奏分析**：紧张/放松/悲伤/愉悦四维追踪

### 🧠 **三层记忆系统**
- **热记忆**：保留最近2章完整内容，细节不丢失
- **温记忆**：保留最近5章摘要，关键剧情不遗忘
- **冷记忆**：长期伏笔追踪，全局设定一致性

### 🎯 **精准改写引擎**
- 质检失败时，只改写问题段落，非全章重来
- 最大3轮改写尝试，避免无限循环
- 400字改写窗口，精准定位问题区域

### 📚 **五维书房体验**
- **阅读模式**：大字号衬线体，首字下沉，打字机效果
- **质量雷达图**：六维质量可视化，一目了然
- **情绪曲线**：SVG图表展示全书情绪节奏
- **角色图谱**：力导向图展示人物关系网络
- **大纲视图**：三幕结构 + 章节状态追踪

### 🎨 **主题系统**
- 暖色纸张风格（#FAF6F1 + Noto Serif SC）
- 深色模式一键切换
- 阅读友好型排版设计

## 🏗️ 技术架构

```
User → Frontend (React + TypeScript + Vite)
         ↓ HTTP + SSE
      Backend (FastAPI)
         ↓
    NovelOrchestrator
    ├── OutlineEngine      # 大纲 + 世界观 + 角色
    ├── ChapterWriter      # 章节生成 + 流式输出
    ├── TieredMemory       # 热/温/冷记忆
    ├── QualityGates       # 并行质检
    │   ├── ConsistencyChecker   # L1/L2/L3 一致性
    │   ├── OriginalityChecker   # 模板检测 + 词汇多样性
    │   ├── AlignmentChecker     # 大纲对齐度
    │   └── EmotionalCurveAnalyzer  # 情绪节奏
    └── RewriteEngine      # 定向改写
```

后端 FastAPI + SQLAlchemy + aiosqlite，前端 React 18 + TypeScript + Vite，LLM 走 OpenAI 兼容 API。存储用 SQLite。

## ⚙️ 技术栈

### 后端
<p>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.111.0-009688?style=flat-square&logo=fastapi" alt="FastAPI"></a>
  <a href="https://pydantic-docs.helpmanual.io"><img src="https://img.shields.io/badge/Pydantic-2.7.3-E92063?style=flat-square&logo=pydantic" alt="Pydantic"></a>
  <a href="https://www.sqlalchemy.org"><img src="https://img.shields.io/badge/SQLAlchemy-2.0.30-1C1C1C?style=flat-square" alt="SQLAlchemy"></a>
  <a href="https://docs.python.org/3/"><img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python" alt="Python"></a>
</p>

### 前端
<p>
  <a href="https://react.dev"><img src="https://img.shields.io/badge/React-18.3.1-61DAFB?style=flat-square&logo=react" alt="React"></a>
  <a href="https://www.typescriptlang.org"><img src="https://img.shields.io/badge/TypeScript-5.4.5-3178C6?style=flat-square&logo=typescript" alt="TypeScript"></a>
  <a href="https://vitejs.dev"><img src="https://img.shields.io/badge/Vite-5.3.1-646CFF?style=flat-square&logo=vite" alt="Vite"></a>
  <a href="https://reactrouter.com"><img src="https://img.shields.io/badge/React_Router-6.23.1-CA4245?style=flat-square&logo=react-router" alt="React Router"></a>
</p>

### 数据存储
<p>
  <a href="https://sqlite.org"><img src="https://img.shields.io/badge/SQLite-3.45+-003B57?style=flat-square&logo=sqlite" alt="SQLite"></a>
  <a href="https://aiosqlite.omnilib.dev"><img src="https://img.shields.io/badge/aiosqlite-0.20.0-008080?style=flat-square" alt="aiosqlite"></a>
</p>

## ⚙️ 配置

复制 `.env.example` 为 `.env` 并配置以下关键设置：

```bash
# LLM 配置
NOVELIST_LLM_API_KEY=sk-your-key-here         # OpenAI 兼容 API Key
NOVELIST_LLM_API_BASE=https://api.openai.com/v1 # API 端点
NOVELIST_LLM_MODEL=gpt-4o                     # 主模型
NOVELIST_LLM_FAST_MODEL=gpt-4o-mini           # 快筛检查模型

# 记忆系统
NOVELIST_HOT_CHAPTERS=2                       # 热记忆保留最近N章全文
NOVELIST_WARM_SUMMARY_CHAPTERS=5              # 温记忆保留最近N章摘要
NOVELIST_MAX_CONTEXT_TOKENS=64000             # 最大上下文长度

# 质量门禁阈值
NOVELIST_NGRAM_OVERLAP_THRESHOLD=0.15         # 句式重复触发阈值
NOVELIST_TEMPLATE_SIMILARITY_THRESHOLD=0.7    # 模板化触发阈值
NOVELIST_VOCAB_DIVERSITY_THRESHOLD=0.4        # 词汇多样性最低阈值
NOVELIST_TWIST_DENSITY_MIN=0.00033            # 每3000字至少1次转折
NOVELIST_ALIGNMENT_SCORE_MIN=0.75             # 大纲对齐最低分
```

完整的配置选项请参考 `.env.example` 文件。

## 🗺️ 路线图

### 🚧 进行中
- **本地模型集成**：Ollama / llama.cpp 支持
- **多语言输出**：英文、日文、韩文创作支持
- **插件系统**：自定义质检规则、风格模板

### 📅 计划中
- **协作创作**：多人实时协作写小说
- **语音朗读**：AI 语音朗读生成章节
- **多格式导出**：EPUB、PDF、Word 格式
- **云端同步**：跨设备同步创作进度

### 💡 未来展望
- **AI 插画生成**：章节配图自动生成
- **角色语音包**：角色专属语音合成
- **剧本模式**：小说转剧本格式
- **出版助手**：投稿格式自动排版

<!--
## 📈 星标历史

[![Star History Chart](https://api.star-history.com/svg?repos=ZhaoDezhang9/ai-novelist&type=Date)](https://star-history.com/#ZhaoDezhang9/ai-novelist&Date)
-->

## 👥 贡献

我们欢迎各种形式的贡献！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献指南。

### 贡献方式
1. 🐛 报告 Bug
2. 💡 提出新功能建议
3. 📖 改进文档
4. 🔧 提交代码修复
5. 🌐 翻译改进

### 开发环境设置
```bash
# 克隆仓库
git clone https://github.com/ZhaoDezhang9/ai-novelist.git
cd ai-novelist

# 设置开发环境
pip install -r requirements-dev.txt  # 如果存在
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 运行开发服务器
uvicorn backend.main:app --reload --port 8000
# 另一个终端
cd frontend && npm run dev
```

## 📄 许可证

MIT License - 你可以随意使用、修改、分发，甚至用于商业项目。

## 🌐 生态兼容

- **支持所有 OpenAI 兼容 API**：DeepSeek、Qwen、GLM、OpenAI、Anthropic...
- **本地模型支持**：计划中的 Ollama / llama.cpp 集成
- **多语言支持**：中文优先，英文完整支持

---

<p align="center">
  <sub>Built with ❤️ by <a href="https://github.com/ZhaoDezhang9">ZhaoDezhang9</a></sub>
</p>