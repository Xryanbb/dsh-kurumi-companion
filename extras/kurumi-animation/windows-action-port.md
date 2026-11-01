# Windows 大肥鱼动作参考与狂三移植范围

## GitHub 参考

- Windows 原生实现：**dsqrwym 和 FeiYu contributors**，[DaFeiYu-Desktop-Pet](https://github.com/dsqrwym/DaFeiYu-Desktop-Pet/tree/7cc743bc80504ac701a6495d01464ecfbccdf65c)。此版本有 100 段动画，其中 97 段可在右键菜单选择、89 段进入随机播放池；还包括三阶段睡眠、5 种随机点击回应、自主走动、拖拽/甩动、鼠标跟随转向、点击走向和打字触发。
- 动作目录与特殊片段区间：[clips.rs](https://github.com/dsqrwym/DaFeiYu-Desktop-Pet/blob/7cc743bc80504ac701a6495d01464ecfbccdf65c/crates/feiyu-app/src/pet/clips.rs)。类别包括转向、移动、小动作、玩耍、饮食、时节、文字、点击回应、说话和工作状态。
- 拖拽后的运动逻辑：[motion.rs](https://github.com/dsqrwym/DaFeiYu-Desktop-Pet/blob/7cc743bc80504ac701a6495d01464ecfbccdf65c/crates/feiyu-core/src/motion.rs)。包含拖动采样、甩出速度、重力、摩擦、边缘反弹和落地。
- 打包方式：上游逐帧动画以 24 fps 播放；Windows 包把画面和 1-bit 透明遮罩分开保存。Windows 仓库里的动画图帧并非狂三素材。

## 狂三侧首批动作

先保留用户批准的狂三角色外观，用独立透明帧组映射状态。早期预览里有循环序列；当前安装器改为静态状态姿态与事件触发单次动作：

| 状态/菜单 | 狂三动作 | 帧数与节奏 |
| --- | --- | --- |
| 待机 `IDLE` | 批准的狂三立绘 | 静止 |
| 思考/等待 `THINKING`、`WAITING` | 狂三静态思考姿态 | 状态持续时保持静止 |
| 工作 `WORKING` | 狂三静态工作姿态 | 状态持续时保持静止 |
| 完成 `SUCCESS` / “开心招手” | 轻抬手起势、两次轻挥、自然放下手臂并回到待机 | 2 张入场 + 4 个主体姿势 + 4 张收势，事件触发后单次播放 |
| 摸头回应 `head_pat` | 眯眼、微倾、含笑回正 | 9 帧，120ms/帧，单次播放 |
| 戳击回应 `poke` | 惊讶、回弹、鼓脸、回正 | 8 帧，120ms/帧，单次播放 |
| 碰发饰 `hair_ribbon` | 回眸、抬手整理红色发带、放手回正 | 9 帧，120ms/帧，单次播放 |
| 空闲小动作 | 当前关闭自动播放 | 仅响应状态事件和用户互动 |
| 拖拽 | 当前姿态图配合原生变形/拖拽反馈 | 尚无专属逐帧拖拽片段 |

透明帧贴图和动作菜单覆盖四种 DSH 状态与三种角色交互。Windows 目录中的自主走动、拖拽抛出物理、鼠标跟随转向、打字触发和三阶段睡眠仍未移植；对应的狂三图帧与行为触发也尚未实现。狂三没有动物尾巴，所以点击发饰区触发“整理发带”，不会使用大肥鱼的尾巴动作。

## 图帧和授权边界

本地 `extras/kurumi-skin/images/` 保存静态姿态 PNG，`extras/kurumi-skin/animations/` 保存原有 60 张狂三关键帧。新增的 6 张挥手姿态保存在 `extras/kurumi-animation/generated/`，安装时复制到 v3 皮肤目录；`SUCCESS` manifest 明确包含 `enter`、`body`、`exit` 三段，播放器以 60 Hz 平滑混合相邻关键帧，最后一帧回到批准待机图。新版挥手逐帧按批准待机图的可见高度和脚底基线归一，宽姿势有画布边界约束；每个 120ms 节拍先展示稳定姿势，再在末尾 45% 时长完成缓和过渡，以减少整身缩放跳变和长时间叠影。单帧读取失败会回退到对应静态姿态。当前是 60 Hz 插值的关键帧动画，不是 24fps 原生帧动画。

Windows 项目代码（`crates/`、`tools/`）采用 MIT，Copyright © 2026 dsqrwym and FeiYu contributors；其 [NOTICE.md](https://github.com/dsqrwym/DaFeiYu-Desktop-Pet/blob/7cc743bc80504ac701a6495d01464ecfbccdf65c/NOTICE.md) 将动画与人物素材单独列出，要求署名、非商业使用及相同方式共享，素材上游为 PC2005-cloud/dsh-pet。我们只借鉴并移植平台无关的动作目录/状态规则，不复制大肥鱼帧图，不把其媒体资产并入狂三皮肤。若将来复用任何代码或素材，发布时再按对应许可保留完整来源和 NOTICE。

## 当前验证状态

- 已对照 Windows 项目的动作目录、状态分类、拖拽物理和逐帧媒体打包方式。
- `PetController.swift` 加载单次序列并惰性缓存纹理；自动小动作已关闭，减少动态效果时冻结循环帧。安装器只映射静态状态图、完成动作和三种点击动作。
- 60 张狂三动作帧已从九格表逐一裁切；戳击图表里的漫画符号帧已排除。另新增 6 张高分辨率挥手关键帧，用明确入场/主体/收势顺序接入 `SUCCESS`。串格的 v2/v3、越界的 v5 wave 和越界的 v8 work 草稿未接入皮肤。详情见 [`generated/README.md`](generated/README.md)。
- 源码编译/安装器配置核对完成后，还需在实际 DSH 宿主播放并检查状态打断、空闲动作间隔和动作过渡；七组小型序列不等同 Windows 的 100 段动作库。
