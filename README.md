<h1 align="center">image-by-sensenova</h1>

<p align="center"><b>商汤 SenseNova 文生图 Agent Skill —— 默认无水印、最高画质、先问清意图再生成。</b></p>

<p align="center">
  <img alt="skill version 0.1.0" src="https://img.shields.io/badge/skill_version-0.1.0-2563eb">
  <img alt="runtime: python3 stdlib" src="https://img.shields.io/badge/runtime-python3_stdlib-lightgrey">
  <img alt="model: sensenova-u1.5-lite" src="https://img.shields.io/badge/model-sensenova--u1.5--lite-4ECDC4">
  <a href="LICENSE"><img alt="license: CC-BY-NC-SA-4.0" src="https://img.shields.io/badge/License-CC--BY--NC--SA--4.0-lightgrey"></a>
</p>

> 私有仓库，shields.io 读不到动态数据，徽章均为静态（随发版手改）。

## 它做什么

调用商汤 [SenseNova Token Plan](https://www.sensenova.cn/token-plan) 文生图模型（当前 `sensenova-u1.5-lite`）生成图片。区别于「拿到一句话就直接画」：

- **先问清，再生成**：主体 / 画幅 / 风格 / 光影 / 构图 / 负面约束 / 复现意图，钉到可执行程度才写 prompt。
- **默认无水印、最高画质**：`watermark: false` + 大尺寸 + PNG 无损 + `b64_json` 直接落盘（不依赖 1 小时过期的 OSS 链接）。
- **每图带元数据**：同编号 `.txt`，含完整参数与 prompt 全文，便于复现与资产管理。
- **8 种常见比例 + 自定义**：1:1 / 16:9 / 9:16 / 4:3 / 3:4 / 3:2 / 2:3 / 21:9，均为 API 实测通过的尺寸。
- **单张 + 批量**：批量带断点续传、限流间隔、超时保护。

## 核心约定

| 项 | 默认 |
|---|---|
| 模型 | `sensenova-u1.5-lite`（`u1-fast` 已下线 404） |
| 水印 | 关闭 |
| 画质 | 大尺寸 + PNG |
| 返回 | `b64_json` 直接落盘 |
| Prompt | 英文优先 |
| 元数据 | 每图同编号 `.txt` |

## 安装

把本仓库作为 skill 目录放入你的 agent skills 库（或软链）：

```bash
git clone https://github.com/cgartlab/image-by-sensenova.git
# 放到你的 skills 路径，例如：
# ln -s "$PWD/image-by-sensenova" ~/.config/magpie/library/skills/image-by-sensenova
```

配置 API key（二选一，**不要硬编码进 skill 文件**）：

```bash
# 方式一：环境变量
export SENSENOVA_API_KEY=sk-xxxxxxxx
# 方式二：文件
mkdir -p ~/.config/sensenova
echo -n "sk-xxxxxxxx" > ~/.config/sensenova/api_key
```

获取 key：[platform.sensenova.cn](https://platform.sensenova.cn) 注册即用，无需绑卡；Token Plan 公测期免费（每 5 小时 1500 次）。

## 安装与同步

**唯一事实源是本仓库**（`git clone` 下来的这份）。放到 skills 路径后的那份是**快照拷贝**，不会随仓库自动更新：

```bash
# 安装（拷贝）
cp -r image-by-sensenova ~/.config/magpie/library/skills/image-by-sensenova

# 或做软链，让已安装 skill 永远等于仓库
rm -rf ~/.config/magpie/library/skills/image-by-sensenova
ln -s "$PWD/image-by-sensenova" ~/.config/magpie/library/skills/image-by-sensenova
```

改了仓库但没重装 → 已加载的 skill 仍是旧快照。判断是否漂移：

```bash
md5sum SKILL.md ~/.config/magpie/library/skills/image-by-sensenova/SKILL.md
```

## 已验证

- `size-check`：8 个比例预设全部命中真实尺寸规则 ✅
- `models`：`/v1/models` 返回两个图像模型（`sensenova-u1.5-lite`、`sensenova-6.8-flash-lite`）✅
- `gen --size 1024x1024`：真实生成 961KB PNG，像素与请求一致，元数据完整（5471 tokens / 20.5s）✅
- `u1-fast` / `1920x1080`：分别复现 404 / 400，验证错误路径 ✅

## 用法

```bash
# 单张
python scripts/sensenova_gen.py gen \
  -p "A cinematic shot of a cyberpunk city at night, neon lights on wet pavement, volumetric fog" \
  --aspect 16:9 --slug cyberpunk-city

# 批量（JSON: [{id,name,prompt,aspect?,negative?,seed?}]）
python scripts/sensenova_gen.py batch items.json --outdir Render/概念图

# 查当前可用模型（零配额）
python scripts/sensenova_gen.py models

# 校验尺寸规则
python scripts/sensenova_gen.py size-check
python scripts/sensenova_gen.py size-check --size 1920x1080   # → INVALID
```

输出：`<outdir>/0001-<slug>.png` + `<outdir>/0001-<slug>.txt`（元数据）。

## 结构

```
SKILL.md                     # 入口：工作流 + 比例表 + CLI + Anti-Patterns
scripts/sensenova_gen.py     # gen / batch / models / size-check
references/api-contract.md   # 实测契约（端点/参数/响应/错误码）
references/prompt-method.md  # 六段式 prompt + 风格锁 + 类型话术
references/aspect-presets.md # 8 比例 + 自定义规则
CHANGELOG.md
LICENSE                      # CC-BY-NC-SA-4.0
```

## 限制

- 当前 API 仅 text→image（不支持图像输入 / 图像编辑 / 交错图文）。
- `n` 只接受 1（每次 1 张）。
- 尺寸须满足：宽高 32 倍数、512–4096、宽高比 ≤3（或 `auto`）。
- 免费额度 1500 次 / 5 小时。

## License

[CC-BY-NC-SA-4.0](LICENSE) © CGArtLab
