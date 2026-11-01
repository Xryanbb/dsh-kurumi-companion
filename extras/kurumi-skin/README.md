# 时崎狂三桌宠素材包

桌宠主体与状态协议参考 [QCYTSN/dsh-dafeiyu](https://github.com/QCYTSN/dsh-dafeiyu)，原作者与贡献者保有原项目代码和功能贡献。本素材包新增狂三角色素材与 macOS 皮肤动作，不将原桌宠记作本次原创。

`images/` 包含基础姿态和拖起反应。原有 `animations/` 有 60 张透明关键帧：待机、思考、翻书工作、招手、摸头、戳击和整理发带。新增挥手动作使用 6 张高分辨率透明关键帧，分为起势、挥手主体、收势三个阶段；helper 逐帧按批准待机图的可见高度和脚底基线归一，并在 60 Hz 绘制节奏中平滑连接姿势。每个 120ms 节拍先展示稳定姿势，再于末尾 45% 时长完成过渡，缩短叠影时间；动作最后一帧回到待机立绘。基础待机直接使用批准的高分辨率立绘。旧的戳击漫画符号格不会安装。狂三没有动物尾巴，因此没有对应的大肥鱼尾巴动作。这是独立制作的 2D 透明动画，不是 Live2D，也没有复制大肥鱼角色素材。

## 安装选择

需要先安装此分支重新构建的 macOS Helper；上游未包含自定义皮肤功能的旧二进制不会读取这份选择文件。先关闭 DSH，再构建/安装此分支插件；然后在仓库根目录运行：

```sh
node extras/kurumi-skin/install-skin.mjs --dry-run
node extras/kurumi-skin/install-skin.mjs
dsh web
```

安装器把姿态图和关键帧新增到 `$DSH_HOME/dsh-dafeiyu/skins/kurumi-animated-v3/`，并写入 `$DSH_HOME/dsh-dafeiyu/skin.json`（含 `IDLE/THINKING/WAITING/WORKING/SUCCESS` 状态序列和 `INTERACTION_HEAD_PAT/INTERACTION_POKE/INTERACTION_HAIR_RIBBON` 点击动作；等待状态共用思考帧）。`SUCCESS` 挥手按入场、主体、收势顺序播放，并平滑回到待机；空闲动作遵循活动等级间隔，随机在思考与招手之间交替。v2 资源目录保留；已有皮肤选择会先保存为 `skin.json.backup-<timestamp>`。默认 `DSH_HOME` 为 `~/.dsh`；不修改其他插件、频道、模型或凭据，不结束进程。

删除或移走 `skin.json` 后重启，可恢复插件原始皮肤；安装器保留的旧选择备份可用于恢复此前的自定义皮肤。

## 检查

```sh
node --test extras/kurumi-skin/install-skin.test.mjs
```

检查仅在自动创建的临时目录中验证路径、备份与 dry-run，不触及真实 DSH 配置。桌宠代码许可证遵循仓库根目录 [LICENSE](../../LICENSE)；生成素材与角色权利说明见上文。
