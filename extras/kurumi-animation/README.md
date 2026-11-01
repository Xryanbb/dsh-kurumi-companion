# 狂三透明动画制作

2026-10-31：用户明确选择优先还原现用角色、保证动作连贯，采用大肥鱼的透明动画方案。3D 实验稿保留供追溯，不作为当前生产路线。2026-11-01 首批状态动作已生成 34 帧；续作加入摸头、戳击、整理发带三种回应，共 60 张透明关键帧。它们是帧序列，不是生成视频，也不是 24fps 动画片库。

## 已锁定的角色

`reference/idle-approved.png` 是当前安装皮肤的原文件副本，未经重画或缩放。SHA-256：`0679fb64aa9f9bc97e2a8dccee7ce904d534d1fe700391aa8f41499d8b453761`。

保留参考图的两头身、脸型、柔和微笑、画面左红眼右金眼、黑色双马尾、红黑发带、露肩分离袖、束腰蝴蝶结、多层蕾丝裙和短腿黑鞋。不能改成塑料玩偶、几何粗模、校服或其他头身比。

## 关键帧原型

以批准的狂三全身图制作透明 3×3 关键帧表，并逐格核验裁切。七组分别是：待机呼吸/轻摆、视线与歪头思考、翻书扫读与眨眼、招手、摸头回应、戳击回应和整理发带。待机、思考和工作循环播放；招手与交互回应单次播放。macOS helper 将每张帧 alpha 裁边并放入共同画布，帧尾做短交叉淡化。

母提示词和早期设计见 `idle-production.json` 与 `idle-prompt.md`。生成的视频服务没有参与本轮；Runway 免费账号也没有消耗或购买额度。

## 关键帧预览

下方 GIF 用于查看动作顺序与角色一致性；预览保留源帧，不模拟 helper 的帧尾交叉淡化。

| 待机 | 思考 / 等待 |
| --- | --- |
| ![狂三待机循环](generated/kurumi-idle-preview.gif) | ![狂三思考循环](generated/kurumi-thinking-preview.gif) |

| 翻书工作 | 开心招手 |
| --- | --- |
| ![狂三翻书工作循环](generated/kurumi-working-preview.gif) | ![狂三开心招手](generated/kurumi-wave-preview.gif) |

| 摸头回应 | 戳击回应 | 整理发带 |
| --- | --- | --- |
| ![狂三摸头回应](generated/kurumi-head-pat-preview.gif) | ![狂三戳击回应](generated/kurumi-poke-preview.gif) | ![狂三整理发带](generated/kurumi-hair-ribbon-preview.gif) |

点击右侧发饰区域播放“整理发带”。狂三没有动物尾巴，因此没有尾巴点击交互。

Windows 动作参考和狂三移植边界见 [`windows-action-port.md`](windows-action-port.md)。优先复用 Windows 版的大量动作状态、触发节奏和拖拽物理，保持狂三身份；大肥鱼角色帧图不当作狂三素材。

## 制作与验收

1. 检查完整角色轮廓、配饰、裙边、书本与眼睛；已发现的越格拼图稿留作未采用草稿，不放入安装目录。
2. 在透明层上按正常速度查看循环，重点核对首尾回接、帧间跳动和脚底位置；静态接触表不能替代实际桌面播放。
3. 通过皮肤安装器把关键帧作为独立序列接入原生 helper；不覆盖大肥鱼默认动画资源，不假定 WKWebView 支持 VP9 alpha。
4. 真机运行验收仍需在 DSH 宿主中确认所有状态切换、循环速度、拖拽与点击反馈；通过前不宣称完成 Windows 版的动作丰富度。

## 来源及新增内容

- 桌宠代码与动作状态机：**QCYTSN 及贡献者**，[dsh-dafeiyu](https://github.com/QCYTSN/dsh-dafeiyu)。
- 透明动画制作流程与首尾姿态参考：**PC2005-cloud 及贡献者**，[dsh-pet 制作指南](https://github.com/PC2005-cloud/dsh-pet/blob/608ed4e49de8003f2e00be0d02976765fe5cc441/MAKE-YOUR-OWN-PET.md)。该项目使用 AI 生成视频，不是公开的可编辑 3D 骨骼模型。其当前说明将代码与动画/提示词许可分开，不能概括为所有素材均为 MIT；本目录未复制其角色素材、提示词全文或处理脚本。
- 双击喂食交互参考：**1190fasheqi 及贡献者**，[dafeiyu-pet](https://github.com/1190fasheqi/dafeiyu-pet/tree/5b0e01856116bd2bae82df1f43c32faa5f056196)。该项目使用正侧背精灵图，不提供本任务所需的人形 3D 骨骼。
- Windows 动作目录与拖拽物理参考：Copyright © 2026 **dsqrwym and FeiYu contributors**，[DaFeiYu-Desktop-Pet](https://github.com/dsqrwym/DaFeiYu-Desktop-Pet/tree/7cc743bc80504ac701a6495d01464ecfbccdf65c)。本项目新增的是狂三动作映射与 macOS 适配；不复制该项目的大肥鱼图帧。代码和动画素材授权分开声明，若再分发素材按该版本 [NOTICE](https://github.com/dsqrwym/DaFeiYu-Desktop-Pet/blob/7cc743bc80504ac701a6495d01464ecfbccdf65c/NOTICE.md) 处理。
- 本分支新增：狂三角色一致性要求、待机表演设计、制作记录和针对桌宠循环的验收规则。狂三角色权利归《约会大作战》相应权利人，不宣称角色原创。

## 当前状态

60 张透明帧和状态映射已准备；生成 GIF 仅用于预览切帧顺序，不包含 helper 的交叉淡化效果。首次 34 帧版本曾安装到 `$DSH_HOME`；本轮加入的交互帧需要随新 Helper 更新后，由 DSH 宿主重启并验收实际播放。当前动作数量仍远少于 Windows 参考的 100 段。
