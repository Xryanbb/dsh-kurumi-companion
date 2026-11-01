# 时崎狂三桌宠素材包

桌宠主体与状态协议参考 [QCYTSN/dsh-dafeiyu](https://github.com/QCYTSN/dsh-dafeiyu)，原作者与贡献者保有原项目代码和功能贡献。本素材包新增狂三角色素材与 macOS 皮肤动作，不将原桌宠记作本次原创。

`images/` 包含基础姿态和拖起反应。`animations/` 有 60 张透明关键帧：7 张待机帧、9 张思考帧、9 张翻书工作帧、9 张招手帧，以及摸头 9 张、戳击 8 张、整理发带 9 张。交互动作按 120ms/帧单次播放；状态循环与空闲动作节奏见安装配置。戳击素材表里的漫画感叹号格未进入安装序列。原生 helper 在帧尾交叉淡化，眨眼仍由眼部局部融合完成。狂三没有动物尾巴，因此没有对应的大肥鱼尾巴点击动作。这是关键帧原型，不等同大肥鱼 Windows 的 24fps 百段动作库，也不是 Live2D 模型。角色为《约会大作战》的时崎狂三；这些新生成图片属于同人素材，非官方素材。

## 安装选择

需要先安装此分支重新构建的 macOS Helper；上游未包含自定义皮肤功能的旧二进制不会读取这份选择文件。先关闭 DSH，再构建/安装此分支插件；然后在仓库根目录运行：

```sh
node extras/kurumi-skin/install-skin.mjs --dry-run
node extras/kurumi-skin/install-skin.mjs
dsh web
```

安装器把姿态图和关键帧新增到 `$DSH_HOME/dsh-dafeiyu/skins/kurumi-animated-v2/`，并写入 `$DSH_HOME/dsh-dafeiyu/skin.json`（含 `IDLE/THINKING/WAITING/WORKING/SUCCESS` 状态序列和 `INTERACTION_HEAD_PAT/INTERACTION_POKE/INTERACTION_HAIR_RIBBON` 点击动作；等待状态共用思考帧）。空闲动作遵循活动等级间隔，随机在思考与招手之间交替。旧的皮肤素材保留；已有皮肤选择会先保存为 `skin.json.backup-<timestamp>`。默认 `DSH_HOME` 为 `~/.dsh`；不修改其他插件、频道、模型或凭据，不结束进程。

删除或移走 `skin.json` 后重启，可恢复插件原始皮肤；安装器保留的旧选择备份可用于恢复此前的自定义皮肤。

## 检查

```sh
node --test extras/kurumi-skin/install-skin.test.mjs
```

检查仅在自动创建的临时目录中验证路径、备份与 dry-run，不触及真实 DSH 配置。桌宠代码许可证遵循仓库根目录 [LICENSE](../../LICENSE)；生成素材与角色权利说明见上文。
