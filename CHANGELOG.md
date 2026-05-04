# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-05-04

### Added
- Initial release of AI Novelist
- Full novel generation pipeline from single idea to complete book
- Tiered memory system (hot/warm/cold) for consistent long-form storytelling
- Quality control system with 4 parallel gates:
  - Consistency checking (L1/L2/L3)
  - Originality detection and vocabulary diversity
  - Outline alignment verification
  - Emotional curve analysis
- Reader mode with 5 interactive analysis tabs:
  - Reading view with typographic enhancements
  - Quality radar visualization (6 dimensions)
  - Emotional curve tracking (4 dimensions)
  - Character relationship force-directed graph
  - Three-act structure outline tracker
- Dark/light theme toggle with paper-like styling
- Streaming chapter generation with real-time updates
- Targeted rewrite engine for precise editing
- Support for multiple novel genres and writing styles
- OpenAI-compatible API support (works with DeepSeek, Qwen, GLM, etc.)
- Full Chinese/English bilingual interface
- FastAPI backend with SQLite storage
- React frontend with TypeScript and Vite
- MIT license - open source and freely modifiable