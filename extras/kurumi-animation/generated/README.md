# 狂三逐帧素材试稿与验收

这些都是基于已批准狂三图像生成的动作关键帧；未复制大肥鱼角色帧。切格采用本目录 `scripts/crop-sprite.swift`，其像素坐标裁切并支持中排微调；预览 GIF 使用 `scripts/preview-idle.swift`，按原顺序显示静态关键帧，不包含 helper 的 28% 帧尾交叉淡化。

## 已采用

- `kurumi-idle-sheet-v4.png`、`idle-frames-v4/`：9 格完整，7 张睁眼帧选入皮肤待机循环；2 张闭眼格继续由眼部局部融合负责。
- `kurumi-wave-sheet-v6.png`、`wave-frames-v6/`、`kurumi-wave-preview.gif`：9 张完整动作帧，包含抬手、左右摆动与收势；接入 `SUCCESS` 单次序列。
- `kurumi-thinking-sheet-v7.png`、`thinking-frames-v7/`：9 张完整思考帧；中排从上边缘内缩 20px 去掉邻行鞋子残片；接入 `THINKING` 循环。
- `kurumi-working-sheet-v9.png`、`working-frames-v9/`：9 张完整翻书帧；接入 `WORKING` 循环。
- `kurumi-idle-preview.gif`、`kurumi-thinking-preview.gif`、`kurumi-working-preview.gif`：按原始帧间隔排列的预览。

## 交互动作续作

- `interaction-sheets-v1/` 保存三张新生成的动作表：摸头回应、戳击回应、整理发带。九格原图与逐帧裁切都保留，便于复查。
- `head-pat-frames-v1/`、`poke-frames-v1/`、`hair-ribbon-frames-v1/` 是裁切后的透明帧。戳击原表第 3 格含漫画感叹号，安装与预览都跳过该格，并把余下 8 帧重新编号。
- 三段交互以 120ms/帧单次播放。相邻动作使用独立帧序列，不把摸头、戳击或整理发带伪装为招手。
- `kurumi-head-pat-preview.gif`、`kurumi-poke-preview.gif`、`kurumi-hair-ribbon-preview.gif` 是动作示例；不包含原生 helper 的姿态淡化。

生成过程中还做过早期排版、越界招手和串格翻书试稿；它们未进入皮肤，也不放入 GitHub 发行内容。当前安装素材目录只放已采用帧。七个序列共 60 张透明关键帧，是交互动作原型，不等同 Windows 参考版 24fps、100 段动作库。GIF 只是关键帧顺序预览；真实 macOS helper 播放仍待宿主验收。
