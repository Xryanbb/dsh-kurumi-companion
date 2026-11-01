# DSH 时崎狂三桌宠（macOS）

这是单独维护的狂三桌宠扩展项目，GitHub 仓库不属于 fork。它把狂三透明动作帧接到 DSH 大肥鱼插件的状态协议与 macOS 原生 Helper 上；需要另行安装官方 [QCYTSN/dsh-dafeiyu](https://github.com/QCYTSN/dsh-dafeiyu)。原作者和贡献者保有原项目代码及功能的署名。

当前有 60 张独立透明帧，组成待机、思考、翻书、招手、摸头回应、戳击回应和整理发带七组动作。另新增一段分为入场、主体和收势的挥手动作，首尾回到批准的待机立绘；相邻姿势按待机图的可见高度与脚底基线对齐，减少手臂抬起时整身缩放跳变，并在每拍末尾短暂淡入下一姿势。空闲时会按 DSH 活动等级间隔轮换思考与招手；新任务会打断装饰动作。狂三没有动物尾巴，点击发饰区域播放整理发带动作。

| 待机 | 思考 / 等待 |
| --- | --- |
| ![狂三待机](extras/kurumi-animation/generated/kurumi-idle-preview.gif) | ![狂三思考](extras/kurumi-animation/generated/kurumi-thinking-preview.gif) |

| 翻书工作 | 开心招手 |
| --- | --- |
| ![狂三翻书工作](extras/kurumi-animation/generated/kurumi-working-preview.gif) | ![狂三招手](extras/kurumi-animation/generated/kurumi-wave-preview.gif) |

| 新版分段招手（入场 → 主体 → 收势回待机） |
| --- |
| ![狂三分段招手](extras/kurumi-animation/generated/kurumi-wave-v2-preview.gif) |

| 摸头回应 | 戳击回应 | 整理发带 |
| --- | --- | --- |
| ![狂三摸头回应](extras/kurumi-animation/generated/kurumi-head-pat-preview.gif) | ![狂三戳击回应](extras/kurumi-animation/generated/kurumi-poke-preview.gif) | ![狂三整理发带](extras/kurumi-animation/generated/kurumi-hair-ribbon-preview.gif) |

旧预览 GIF 展示透明帧顺序，不包含 Helper 的姿态混合。新版招手预览按 Helper 的可见高度和脚底基线对齐，再生成缓和过渡画面。详细的动作对应和来源见 [Windows 动作参考](extras/kurumi-animation/windows-action-port.md)、[素材提示词](extras/kurumi-animation/generated/wave-prompt-v3.md) 与 [NOTICE](NOTICE.md)。

## 安装

需要 macOS 12+、Node.js 和 Xcode Command Line Tools。先完全退出 DSH Host，再在本项目根目录运行：

```sh
# Web profile 默认位置；桌面 profile 可将此变量改为对应插件目录
export DSH_DAFEIYU_ROOT="$HOME/.dsh/profiles/web/node_modules/dsh-dafeiyu"

native/macos/build-helper.sh
scripts/install-helper.sh
node extras/kurumi-skin/install-skin.mjs --dry-run
node extras/kurumi-skin/install-skin.mjs
```

重新启动 DSH Host 后生效。`install-helper.sh` 会把旧 Helper 移到 `~/.dsh/dsh-dafeiyu/backups/`；安装器会备份原 `skin.json`，旧皮肤目录保留。脚本不会结束 DSH 进程，也不读取或更改模型凭据。

只想预览安装配置时，运行带 `--dry-run` 的命令即可。要恢复旧版，可退出 DSH，将备份 Helper 移回插件目录，并恢复 `skin.json` 备份后重启。

## 项目边界

- DSH 大肥鱼插件负责会话事件；本项目提供 macOS Helper 的狂三动作适配和皮肤素材。
- Helper 代码基于原 DSH 桌宠实现；本仓库没有复制大肥鱼角色帧。
- 这是透明关键帧方案，不是 Live2D 或 Windows 版的 100 段动作库。
- 时崎狂三属于《约会大作战》角色；相关图片为非官方同人素材，素材说明见 [ASSET_LICENSE.md](ASSET_LICENSE.md)。
- 此次新增点击动作尚未完成 DSH 宿主重启后的真机播放验收。

## 来源

主体项目：**QCYTSN 及贡献者**，[dsh-dafeiyu](https://github.com/QCYTSN/dsh-dafeiyu)。Windows 动作状态与交互节奏参考 **dsqrwym 和 FeiYu contributors** 的 [DaFeiYu-Desktop-Pet](https://github.com/dsqrwym/DaFeiYu-Desktop-Pet)；未复制其角色图帧。
