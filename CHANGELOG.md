# Changelog

本仓库的显著变更记录。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 文档

- README 补「安装与同步」（仓库为事实源、安装是快照拷贝、漂移自检）与「已验证」实测清单。
- CHANGELOG 顶部补 Unreleased 段，避免改动只在提交信息里留痕。
- 新增 `AGENTS.md`：agent 在本仓库的工作约定（先跑 `models` 核实事实、不硬编码 key、生成产物不入库）。
- 开发记录：旧 `img-sensenova`（三江源专用版）已从 magpie library 删除，仅保留本仓库的通用 skill，消除双技能选择歧义。

## [0.1.0] - 2026-10-22

首个可用版本。重构为通用 SenseNova 文生图 skill。

### 新增

- `SKILL.md`：通用入口，强制「先问清意图再生成」工作流，8 种常见比例预设，Anti-Patterns。
- `scripts/sensenova_gen.py`：单条命令四子命令 —— `gen`（单张）、`batch`（JSON 批量，断点续传 + 限流）、`models`（查模型清单，零配额）、`size-check`（校验尺寸规则）。
- 每图同编号 `.txt` 元数据：model / size 请求与响应 / 实际像素 / seed / watermark / prompt 全文 / negative / usage tokens / 时间戳 / 耗时 / 字节数。
- `references/api-contract.md`：端点、参数、响应、错误码、实测记录（含 `u1-fast` 已 404、真实尺寸规则、两图像模型）。
- `references/prompt-method.md`：六段式结构、风格锁、负面词、按画面类型的话术变体。
- `references/aspect-presets.md`：8 比例预设 + 自定义尺寸推导规则。
- `LICENSE`（CC-BY-NC-SA-4.0）、`README.md`、`.gitignore`、`CHANGELOG.md`。

### 修正（相对旧版 D:\github-repos 散装 SKILL.md）

- 模型 `sensenova-u1-fast` → `sensenova-u1.5-lite`（u1-fast 已下线，404）。
- 尺寸规则改正：非固定尺寸表，而是「宽高 32 倍数、512–4096、宽高比 ≤3」或 `auto`。
- `output_tokens` 实测 4096–5500（旧文档误记「固定 16384」）。
- 默认 `watermark: false`、`response_format: b64_json`、`output_format: png`。
- API key 不再硬编码进 skill 文件，改读环境变量 / `~/.config/sensenova/api_key`。
