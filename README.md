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

## 这不是又一个 AI 写作工具

市面上有太多"AI 写小说"的产品，你把灵感扔进去，它吐出一段还不错的文字——然后呢？没有大纲，角色会突变，第三章就忘了第一章埋的伏笔，结尾纯粹是胡扯。

AI 小说家解决的是**整本书创作**的问题。

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

它的品味体现在你不必操心的事情上：

- **它不会让你写重复的话** — 原创性检测会在你察觉之前拦住模板化套路。
- **它记得自己写过什么** — 热记忆保留最近几章的完整内容，温记忆压缩中期剧情，冷记忆追踪伏笔——不会莫名其妙地让已经死了的角色活过来。
- **它改写有针对性** — 如果质检没通过，不是整章重来，而是精准定位到出问题的那几个段落，只改那些地方。
- **它自带书房** — 不只是看字，还有质量雷达图、情绪曲线、角色关系图谱——让你这个作者知道你的书到底写得怎么样。

## 首次使用

```bash
# 1. 安装
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 2. 配置你的 API Key
cp .env.example .env
# 编辑 .env → 把 NOVELIST_LLM_API_KEY 换成你自己的 Key

# 3. 启动
./启动.bat
```

打开浏览器，访问 **http://localhost:3000**

在创作页写下一句灵感，点击"AI 生成标题和主题"，然后开始创作。

## 它长什么样

### 创作页 —— 灵感入口

左侧是表单：类型标签（修仙/玄幻/都市/科幻/灵异/历史/武侠/奇幻）、风格选择（古典雅致/轻松诙谐/热血激昂/诗意唯美/冷峻写实）、章节数和字数控制。右侧是实时预览卡片，你每改一个字，预览就跟着变。

### 书房 —— 不只是看小说

五个标签页：

- **阅读** — 传统章节阅读，大字号衬线体，每段首字下沉。支持打字机效果模式。
- **质量检测** — 六维雷达图：一致性、原创性、大纲对齐、情感曲线、文笔质量、伏笔回收。
- **情绪曲线** — 紧张/放松/悲伤/愉悦四维度追踪整本书的情绪节奏。
- **角色图谱** — 力导向图展示角色关系，谁和谁是道侣，谁在暗算谁。
- **大纲** — 三幕结构 + 每章节拍目标，一眼看清哪些章节已写完、哪些待创作。

### 深色 / 浅色

暖色纸张风格是默认主题（#FAF6F1 背景 + Noto Serif SC 衬线体），点一下月亮图标切换深色模式。

## 为什么选择 AI 小说家

| | AI 小说家 | 在线 AI 写作工具 |
|---|---|---|
| 代码 | 开源，可修改 | 闭源，不可见 |
| 数据 | 完全本地，你的内容你做主 | 传输到对方服务器 |
| 模型 | OpenAI 兼容 API，可接任何模型 | 绑死官方模型 |
| 创作流程 | 大纲→章节→质检→改写，完整闭环 | 只能单次生成 |
| 长篇记忆 | 热/温/冷三层记忆 | 靠 prompt 硬塞，超出窗口就忘 |
| 可视化 | 雷达图/情绪曲线/角色图谱 | 无 |

## 技术架构

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

## 生态 & 许可

- 支持所有 OpenAI 兼容 API（DeepSeek、Qwen、GLM、OpenAI、Anthropic...）
- 本地模型支持计划中（Ollama / llama.cpp）

MIT License — 随便用，随便改，随便拿去卖钱。

---

<p align="center">
  <sub>Built with ❤️ by <a href="https://github.com/ZhaoDezhang9">ZhaoDezhang9</a></sub>
</p>
