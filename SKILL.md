---
name: image-by-sensenova
description: 用商汤 SenseNova 系列文生图模型生成图片。当用户说"用 sensenova 画图/生图""文生图 sensenova""u1.5-lite 生图""生成信息图/概念图/设定图"时激活。默认无水印、最高画质、PNG；生成前主动提问澄清意图，产出图片 + 同编号 .txt 元数据（含完整参数与提示词）。支持 1:1/16:9/9:16/4:3/3:4/3:2/2:3/21:9 常见比例与自定义尺寸，单张与批量。
triggers:
  - "/image-by-sensenova"
  - "sensenova 图片生成"
  - "用 sensenova 画图"
  - "文生图 sensenova"
  - "u1.5-lite"
  - "sensenova 生图"
tools:
  - exec
mutating: false
license: CC-BY-NC-SA-4.0
compatibility: 需 Python 3（纯标准库，无 pip 依赖）；可选环境变量 SENSENOVA_API_KEY 或 ~/.config/sensenova/api_key。
metadata:
  version: "0.1.0"
  date: "2026-10-22"
  reference: "https://github.com/cgartlab/image-by-sensenova"
---

# image-by-sensenova — SenseNova 文生图 Skill

调用商汤 [SenseNova Token Plan](https://www.sensenova.cn/token-plan) 文生图模型（当前可用 `sensenova-u1.5-lite`）生成图片。

## 核心约定（默认值，除非用户另行要求）

| 项 | 默认 | 说明 |
|---|---|---|
| 模型 | `sensenova-u1.5-lite` | 唯一在役图像模型；`u1-fast` 已下线（404） |
| 水印 | **关闭** (`watermark: false`) | 不带「日日新」品牌水印 |
| 画质 | **最高**：大尺寸 + PNG 无损 | 见比例表，均可到 3072–4096 量级 |
| 返回 | `b64_json` | 直接落盘，不依赖 1 小时过期的 OSS 链接 |
| Prompt 语言 | **英文优先** | 英文画面控制力远胜中文；中文易乱码 |
| 元数据 | 每图同编号 `.txt` | 完整参数 + prompt + usage，便于复现与资产管理 |

## 工作流（强制：先问清，再生成）

> **每次收到生图需求，必须先用提问把意图钉到可执行程度，再写 prompt 调 API。** 不要拿到一句话就直接生成。

收到需求后，按需问清（一次集中问，不要挤牙膏）：

1. **主体与含义**：画什么？谁/什么物体/什么场景？要传达什么？
2. **画幅**：1:1 / 16:9 / 9:16 / 4:3 / 3:4 / 3:2 / 21:9 / 自定义？（不指定默认 1:1）
3. **风格**：电影剧照 / 信息图 / 概念设定 / 水彩 / 写实摄影 / 动漫…（不指定由你按主体给合理默认）
4. **光影与色调**：丁达尔光 / 伦勃朗 / 逆光；冷暖、具体色板？
5. **构图**：视角、主体占比、负空间、留白？
6. **负面约束**：禁文字 / 禁水印 / 禁人物 / 禁特定元素？
7. **数量与复现**：单张还是批量？要不要固定 seed 复现？

信息充足后，按 [`references/prompt-method.md`](references/prompt-method.md) 的六段式组装英文 prompt，再调脚本生成。

## 比例 → 尺寸预设（均为 32 倍数、512–4096、宽高比 ≤3，已实测通过）

| 比例 | 尺寸 | 用途 |
|---|---|---|
| 1:1 | 3072×3072 | 正方形、头像、单图 |
| 16:9 | 4096×2304 | 横屏、电影、桌面 |
| 9:16 | 2304×4096 | 竖屏、手机、海报 |
| 4:3 | 4096×3072 | 经典横画幅 |
| 3:4 | 3072×4096 | 经典竖画幅、海报 |
| 3:2 | 3840×2560 | 摄影、打印 |
| 2:3 | 2560×3840 | 竖版摄影 |
| 21:9 | 4096×1760 | 超宽、电影宽幅 |

> 自定义尺寸必须满足：宽高均为 32 的倍数、512–4096、宽高比 ≤3。`size-check` 子命令可校验。

## CLI 用法

```bash
# 单张：prompt 作为变量传入
python scripts/sensenova_gen.py gen \
  -p "A cinematic shot of a cyberpunk city at night, neon lights on wet pavement, volumetric fog" \
  --aspect 16:9 --slug cyberpunk-city

# 从 stdin 读 prompt（长 prompt 推荐）
echo "..." | python scripts/sensenova_gen.py gen --aspect 1:1 --slug test

# 批量：JSON 文件，每项 {id,name,prompt,aspect?,negative?,seed?}
python scripts/sensenova_gen.py batch batch.json --outdir Render/概念图

# 查询当前可用模型
python scripts/sensenova_gen.py models

# 校验尺寸规则
python scripts/sensenova_gen.py size-check
python scripts/sensenova_gen.py size-check --size 1920x1080
```

**参数（变量）**：`-p/--prompt`、`--negative`、`--aspect`、`--size`、`--seed`、`--style`、`--quality`、`--temperature`、`--format png|jpeg`、`--slug`、`--outdir`、`--model`。完整清单见 `python scripts/sensenova_gen.py gen --help`。

## 输出约定

- 图片：`<outdir>/<编号4位>-<slug>.<format>`（如 `0001-cyberpunk-city.png`）
- 元数据：`<outdir>/<编号4位>-<slug>.txt`，含 model / size（请求与响应）/ 实际像素 / seed / watermark / prompt 全文 / negative / usage tokens / 时间戳 / 耗时 / 字节数
- 编号在 `--outdir` 内自动递增（扫描已有 `NNNN-*` 取最大 +1）

## API Key

脚本按顺序读取，**不硬编码**：
1. 环境变量 `SENSENOVA_API_KEY`
2. `~/.config/sensenova/api_key` 文件（单行）

获取：[platform.sensenova.cn](https://platform.sensenova.cn) 注册即用，无需绑卡；Token Plan 公测期免费（每 5 小时 1500 次）。

## 配额

| 项 | 值 |
|---|---|
| 免费额度 | 1500 次 / 5 小时（每模型独立） |
| 单次消耗 | input ≈ prompt 长度；output ≈ 4000–5500 tokens（按尺寸） |
| 图片链接 | OSS 临时，1 小时过期 —— 本 skill 用 b64 直接落盘，不受此限 |

## References

- [API 契约（实测）](references/api-contract.md) — 端点、参数、响应、错误码、实测记录
- [Prompt 方法论](references/prompt-method.md) — 六段式结构、风格锁、负面词、类型话术
- [比例与尺寸预设](references/aspect-presets.md) — 推导规则与自定义方法

## Anti-Patterns

- ❌ 不要用 `u1-fast`（已 404）；不要假设模型清单不变（用 `models` 子命令现查）
- ❌ 不要传非 32 倍数的尺寸（如 1920×1080 → 400）
- ❌ 不要忘记 `watermark: false`（默认已带，但手动构造 payload 时别漏）
- ❌ 不要用 `/v1/chat/completions`（图像模型不走 chat 接口）
- ❌ 不要传 `n` > 1（仅 1 有效）
- ❌ 不要把 API key 硬编码进文件
- ❌ 不要不问清意图就直接生成 —— 先澄清，再写 prompt
