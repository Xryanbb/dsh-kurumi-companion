# 狂三逐帧素材试稿与验收

这些都是基于已批准狂三图像生成的动作关键帧；未复制大肥鱼角色帧。切格采用本目录 `scripts/crop-sprite.swift`，其像素坐标裁切并支持中排微调。旧预览 GIF 使用 `scripts/preview-idle.swift` 展示静态关键帧；新挥手 GIF 使用 `scripts/preview-sequence.swift` 生成缓和的相邻帧过渡。

## 已采用

- `kurumi-idle-sheet-v4.png`、`idle-frames-v4/`：9 格完整，7 张睁眼帧选入皮肤待机循环；2 张闭眼格继续由眼部局部融合负责。
- `kurumi-wave-sheet-v6.png`、`wave-frames-v6/`、`kurumi-wave-preview.gif`：旧版 9 张招手帧，留作迭代记录，v3 安装器不再使用。
- `kurumi-thinking-sheet-v7.png`、`thinking-frames-v7/`：9 张完整思考帧；中排从上边缘内缩 20px 去掉邻行鞋子残片；接入 `THINKING` 循环。
- `kurumi-working-sheet-v9.png`、`working-frames-v9/`：9 张完整翻书帧；接入 `WORKING` 循环。
- `kurumi-idle-preview.gif`、`kurumi-thinking-preview.gif`、`kurumi-working-preview.gif`：按原始帧间隔排列的预览。

## 交互动作续作

- `interaction-sheets-v1/` 保存三张新生成的动作表：摸头回应、戳击回应、整理发带。九格原图与逐帧裁切都保留，便于复查。
- `head-pat-frames-v1/`、`poke-frames-v1/`、`hair-ribbon-frames-v1/` 是裁切后的透明帧。戳击原表第 3 格含漫画感叹号，安装与预览都跳过该格，并把余下 8 帧重新编号。
- 三段交互以 240ms/帧单次播放。相邻动作使用独立帧序列，不把摸头、戳击或整理发带伪装为招手。
- `kurumi-head-pat-preview.gif`、`kurumi-poke-preview.gif`、`kurumi-hair-ribbon-preview.gif` 是动作示例；不包含原生 helper 的姿态淡化。

## 整理发带 v2

- `interaction-sheets-v2/kurumi-hair-ribbon-v2-sheet-preview.png` 是内置 imagegen 生成的 3×3 透明动作表缩略图，原图留在本地生成档案；参考已批准的 `reference/idle-approved.png` 和 v1 摸头动作表，角色比例、黑红服装、双马尾和异色瞳按参考图保持，未加入动物尾巴。
- [kurumi-hair-ribbon-prompt-v2.md](kurumi-hair-ribbon-prompt-v2.md) 记录生成提示词。3×3 网格由 CoreGraphics 按像素等分裁切，每格向内缩 8 px 去掉格边碎片；裁切后保留 RGBA 透明通道。采用的 9 张帧位于 `../../kurumi-skin/animations/hair_ribbon_v3/`。
- `kurumi-hair-ribbon-v2-preview-web.gif` 按 240ms/帧播放一次，时长约 2.16 秒；桌宠配置同样为单次播放，并按批准待机立绘归一尺寸，结束返回静止待机。
- 这段是 9 张绘制关键姿势构成的透明序列，不是 24fps 视频；其他交互仍使用 v1 姿势素材。

## v3 挥手分段

- `wave-start-v1.png` 与 `wave-anticipation-v1.png`、`wave-intermediate-v1.png`、`wave-intermediate-v2.png`、`wave-recovery-v1.png`、`wave-lowered-v1.png` 是 6 张高分辨率透明关键帧；起势帧与批准待机图保持 1374×1145 原尺寸，其余动作为 1377×1142。
- 新 `SUCCESS` 时间线：批准待机帧 → 轻抬手起势 → 抬手入场 → 两次挥手主体 → 放下手臂至腰侧 → 轻收手 → 回到批准待机帧。
- `kurumi-wave-v2-preview.gif` 按批准待机图的可见高度、脚底基线与 120ms 关键姿势节拍生成预览；每拍先稳定展示，再在最后 45% 时长淡入下一帧。macOS helper 在窗口绘制时以 60 Hz 采样同一序列。它仍是关键帧插值，不是 24fps 的原生逐帧视频。
- [wave-prompt-v3.md](wave-prompt-v3.md) 记录新增关键帧的整理版生成提示词、各姿势说明和验收约束。

生成过程中还做过早期排版、越界招手和串格翻书试稿；它们未进入皮肤，也不放入 GitHub 发行内容。当前安装素材目录只放已采用帧。原有七组序列共 60 张透明关键帧；新增的 6 张姿势关键帧用于 v3 招手动作，不等同 Windows 参考版 24fps、100 段动作库。真实 macOS helper 播放仍待宿主验收。
