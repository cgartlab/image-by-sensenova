# Prompt 方法论

## 核心原则

- **英文 prompt 远优于中文**：画面控制力、细节准确度、文字/数字渲染都明显更好。中文只用于文件名和元数据。
- **不需要泛泛质量词**：u1.5-lite 原生高分辨率，"高质量""细节丰富""8K""masterpiece" 是冗余。
- **越具体越好**：主体 + 环境 + 光影 + 风格 + 构图，五要素给死。
- **负面词防数字味**：`digital render, CGI, 3D render, smooth gradients, airbrushed, plastic, pristine, uniform outlines, cel shading, anime`。
- **零字幕**：结尾加 `No text, no watermarks, no signatures.`（信息图等需要文字的场景除外，但 AI 生成的文字仍可能乱码，关键文字一律后期叠加）。

## 六段式结构（固定顺序）

复杂风格复现按此六段组织 prompt：

```
Generate a <medium> ... Design reasoning in six steps:
1. SUBJECT AND MEANING: <主体 + 含义>
2. FRAME AND COMPOSITION: <视角 / 占比 / 层次 / 负空间 / 节奏>
3. ENVIRONMENT: <环境>
4. LIGHTING AND COLOR: <光影 + 色板，给具体色值如 #E25822>
5. STYLE LOCK: <风格锁——最重要的段落；写材质 / 笔触 / 边缘关系 / 反数字渲染声明>
6. FINAL IMAGE: <一句话终帧描述> No text, no watermark, no signature.
```

### 各段要点

**1. 主体与含义**：画什么、谁、在做什么、要传达什么情绪/概念。动作/事件/因果关系要写明（模型会推理物理逻辑）。

**2. 构图与画幅**：视角（仰角/俯视/平视/航拍）、主体占比（60–80% 为主体 / 留负空间）、层次（前景-中景-远景三层）、节奏（疏密松紧）。

**3. 环境**：地点、天气、时间、氛围元素（雾、尘、雨、碎片…）。

**4. 光影与色彩**：
- 光型：丁达尔体积光 / 伦勃朗光 / 逆光 / 侧光 / 剧场式顶光 / 轮廓光
- 色板：给具体色值（熔岩橙 `#E25822`、暗金赭石 `#9C6B30`、深青钢蓝 `#2A4B5E`、电青 `#4ECDC4`、幻紫 `#7B68EE`）
- 明度策略：低长调（大面积暗 + 小面积高光）最出质感

**5. 风格锁（最关键）**：
- ❌ 只挂艺术家名字（梵高/莫奈）→ 各风格全糊成油画感，拉不开差距
- ✅ 按**绘画工艺/媒介**写：水彩 / 蚀刻 / 水墨 / 丝网 / 玻璃 / 厚涂丙烯… 每种写死材质 + 技法 + 肌理
- ✅ 手绘感关键词（对抗数字渲染味）：`heavy impasto, palette-knife ridges, dry-brush drag, exposed canvas tooth, overpainted messy edges, muddy shadow mixtures, uneven varnish, craquelure, film grain`
- ✅ 绘画关系四件套：`lost-and-found edges（虚实）, tight-loose alternation（松紧）, density variation（疏密）, rhythmic alternation（节奏）`——且声明作用于主体轮廓（受光侧实/背光侧化进暗部），不只背景

**6. 终帧句**：一句话重申画面，接负面约束。

## 按画面类型的变体

### 电影剧照 / 写实摄影
- 主体：`real human actors / live-action movie still / photorealistic`
- 风格锁：`cinematic movie still, anamorphic lens, 35mm film grain, shallow depth of field, blockbuster teal-and-orange grade`
- 负面**反向禁**：`oil painting, brushstrokes, illustration, anime, manga`
- 画幅：16:9（`4096x2304`）
- ⚠️ 已知漂移：u1.5-lite 的「真人写实」易漂回半写实 CGI 动漫质感。对抗：style lock 堆 `real human actors / practical prosthetic suit / film grain / shot on set`，负面禁 `digital render / fan art / 3D render / cosplay`，终帧句重申 `photograph`。仍漂移则接受半写实质感并明示用户。

### 信息图（Infographic）
- 明确分区与数据可视化描述：
  ```
  An infographic about <topic>, divided into N sections: <列举>.
  <背景色> with <文字色> text and <强调色> charts.
  Professional presentation style, clean layout, data visualization
  including bar charts and line graphs.
  ```
- ⚠️ AI 生成的文字仍可能乱码；关键数据/标签一律后期叠加。

### 概念设定图 / 概念艺术
- `Cinematic concept art, <镜头类型>, 16:9 widescreen.`
- 主体 + 场景 + 摄影参数（镜头焦距、光圈）+ 光照 + 调色 + 构图 + 负面
- 空场景禁人物：`No text, no watermarks, no subtitles, no people.`

### 人物多视角板
- `multi-angle character sheet, 6 panels 2x3, unified lighting and proportions, same character across all panels.`
- 统一灯光/比例/同一人物；禁政治人物；人物不看镜头（`gaze off-camera`）

### 道具六视图
- `2x3 grid six-view (front/back/left/right/top/bottom), pure white background, studio lighting.`
- 禁人物/文字/水印

### 色彩情绪板
- `mood board, color study, <色板描述>.`
- 纯色彩研究，无叙事

## 复现与迭代

- 固定 `seed` 可复现同一画面，用于对比风格微调
- 迭代中验证有效的写法，回写本文件，沉淀为可复用资产
- 每次生成的 `.txt` 元数据保留了完整参数，失败的好 prompt 不会丢
