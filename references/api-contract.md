# API 契约（2026-10-22 实测）

端点、参数、响应均经真实请求验证。模型清单与错误码以**当日实测**为准 —— SenseNova 公测期迭代频繁，使用前先跑 `python scripts/sensenova_gen.py models`。

## 端点

| 用途 | 方法 | URL |
|---|---|---|
| 文生图 | POST | `https://token.sensenova.cn/v1/images/generations` |
| 模型列表 | GET | `https://token.sensenova.cn/v1/models` |

认证：`Authorization: Bearer <SENSENOVA_API_KEY>`

## 当前可用模型（2026-10-22）

```
deepseek-v4-flash, glm-5.2, sensenova-6.8-flash-lite,
sensenova-u1.5-lite, kimi-k3, deepseek-flash, deepseek-v4.1-flash
```

- **图像生成模型**（两个，均经 `/v1/models` 确认）：
  - `sensenova-u1.5-lite` —— 默认，画质优先
  - `sensenova-6.8-flash-lite` —— 更快更省，适合批量迭代试稿（未深度实测，可用 `--model` 切换试用）
- ❌ `sensenova-u1-fast` 已下线：传它返回 `404 {"error":{"message":"model is not found","type":"not_found_error","code":"5"}}`

## 请求参数

| 参数 | 类型 | 必需 | 默认 | 说明 |
|---|---|---|---|---|
| `model` | string | ✅ | — | `sensenova-u1.5-lite` |
| `prompt` | string | ✅ | — | 英文效果显著优于中文 |
| `size` | string | ✅ | — | `auto` 或 `WIDTHxHEIGHT`；宽高 32 倍数、512–4096、宽高比 ≤3 |
| `n` | int | ❌ | 1 | **仅 1 有效** |
| `watermark` | bool | ❌ | `true` | **必须传 `false` 关闭水印** |
| `response_format` | string | ❌ | `url` | `url`（OSS，1h 过期）或 `b64_json`（推荐） |
| `output_format` | string | ❌ | `png` | `png` / `jpeg` |
| `negative_prompt` | string | ❌ | `""` | 反向提示词 |
| `seed` | int | ❌ | 随机 | 相同 seed + prompt 可复现 |
| `style` | string | ❌ | — | 视 API 支持，未实测 |
| `quality` | string | ❌ | — | 视 API 支持，未实测 |
| `temperature` | float | ❌ | — | 0.0–1.0 |

> `style` / `quality` / `temperature` 未在 u1.5-lite 上验证是否生效；脚本仅在显式传入时才带这些参数，避免触发未知错误。

## 尺寸规则（400 错误原文）

```
invalid size, should be auto or WIDTHxHEIGHT.
width and height should be multiples of 32,
width and height should be in [512,4096],
and aspect ratio should be within 3:1
```

实测：`1024x1024` ✅、`2016x1120` ✅、`3072x1376` ✅、`4096x2304` ✅；`1920x1080` ❌（1080 非 32 倍数）。

## 响应

```json
{
  "created": 1783854516,
  "data": [{"b64_json": "<base64 PNG>"}],
  "output_format": "png",
  "size": "2016x1120",
  "usage": {
    "input_tokens": 1332,
    "input_tokens_details": {"image_tokens": 0, "text_tokens": 1332},
    "output_tokens": 4128,
    "total_tokens": 5460,
    "images_count": 1
  }
}
```

| 字段 | 说明 |
|---|---|
| `data[0].b64_json` | base64 图片数据（`response_format=b64_json` 时） |
| `data[0].url` | OSS 临时链接（`response_format=url` 时，**1 小时过期**） |
| `size` | 回显的实际尺寸，可用于断言 |
| `output_format` | 回显的输出格式 |
| `usage.output_tokens` | 实测 4096–5500（按尺寸），**不是**旧文档的固定 16384 |
| `usage.images_count` | 固定 1 |

## 错误码

| HTTP | code | 含义 | 对策 |
|---|---|---|---|
| 404 | 5 | `model is not found` | 模型已下线，跑 `models` 查当前可用 |
| 400 | 3 | `invalid size` | 按尺寸规则修正 |
| 401 | — | 认证失败 | 检查 API key |
| 429 | — | 限流 | 降低频率，5 小时 1500 次额度 |

## 实测记录

- 2026-10-22：`u1.5-lite` + `1024x1024` → 成功，output_tokens=4096
- 2026-10-22：`u1.5-lite` + `2016x1120` → 成功，output_tokens=4128，像素精确匹配
- 2026-10-22：`u1.5-lite` + `3072x1376` → 成功，output_tokens=4128
- 2026-10-22：`u1.5-lite` + `1920x1080` → 400（1080 非 32 倍数）
- 2026-10-22：`u1-fast` → 404 model not found
