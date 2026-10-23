# AGENTS.md — image-by-sensenova

给在本仓库工作的 agent 的约定。**这些不是建议，是硬约束。**

## 1. 事实来源

- **API 事实以实时请求为准，不以文档为准。** 开工第一步跑 `python scripts/sensenova_gen.py models`，确认模型 ID 还在。历史上 `sensenova-u1-fast` 静默下线（404 `model is not found`），而文档仍把它写成唯一模型，照文档调用只会失败。
- 文档里的尺寸表、token 数、模型清单都可能过期。写新事实时注明**实测日期**（如「2026-10-22 实测」）。
- 区分「实测事实」「官方文档抄来的」「推测」，三者不得混写。

## 2. 密钥

- **任何时候不要把 key 打印到终端输出、写进 SKILL.md/README、或提交进仓库。**
- 读取顺序：`SENSENOVA_API_KEY` → `~/.config/sensenova/api_key`。
- 需要复用本机 key 时，用正则从配置文件提取后直接使用，只打印「key found: true/false」。

## 3. 生成产物不入库

- `Render/`、`*.png/jpeg/jpg/webp`、`__pycache__/`、`*.pyc` 已在 `.gitignore`。
- 产物如果要长期保留，放外部项目目录，不要往本仓库塞图。

## 4. 改动前后的门槛

- 改 `scripts/sensenova_gen.py` 后必须跑：`size-check`（纯本地，零配额）→ `gen --size 1024x1024`（真实生成 1 张，约 5k tokens）确认端到端可用。
- 不要为了「跑绿」删掉校验逻辑或把真实断言改成 `pass`。
- 配额是 1500 次 / 5 小时，验证只打 1 张，用最小 prompt。

## 5. 版本与发布

- 版本号在 `SKILL.md` frontmatter 的 `metadata.version` 与 `CHANGELOG.md` 顶部章节**同时**维护，必须一致。
- 发布：`git tag -a vX.Y.Z` → push tag → `gh release create`，release notes 从 CHANGELOG 对应章节摘要。
- 纯文档改动走 `docs:` 提交，不单独发版；行为变更才 bump。

## 6. 已安装 skill 与仓库的关系

- 仓库是权威副本；`~/.config/magpie/library/skills/image-by-sensenova` 是安装后的拷贝。
- 改完仓库要么重装拷贝，要么确认该目录是软链到仓库，否则已加载的 skill 与仓库漂移。自检见 README「安装与同步」。
