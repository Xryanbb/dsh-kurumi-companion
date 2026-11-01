# 时崎狂三桌宠素材包

桌宠主体与状态协议参考 [QCYTSN/dsh-dafeiyu](https://github.com/QCYTSN/dsh-dafeiyu)，原作者与贡献者保有原项目代码和功能贡献。本素材包新增狂三角色素材与 macOS 皮肤动作，不将原桌宠记作本次原创。

`images/` 包含基础姿态和拖起反应。旧的 `animations/` 目录保留既有动作帧；当前选择文件不再让待机、思考和工作帧循环播放。点击互动或 DSH 状态事件会单次播放相应透明帧序列，结束回到待机。三种点击动作统一为 240ms/帧；发带动作按静止待机立绘归一尺寸。减少动态效果开启时，循环序列停在首帧，单次互动继续播放。素材仍是关键姿势，不是 24fps 视频片段。狂三没有动物尾巴，因此没有对应的大肥鱼尾巴动作；项目不复制大肥鱼角色素材。

## 安装选择

需要先安装此分支重新构建的 macOS Helper；上游未包含自定义皮肤功能的旧二进制不会读取这份选择文件。先关闭 DSH，再构建/安装此分支插件；然后在仓库根目录运行：

```sh
node extras/kurumi-skin/install-skin.mjs --dry-run
node extras/kurumi-skin/install-skin.mjs
dsh web
```

安装器把姿态图和单次动作帧新增到 `$DSH_HOME/dsh-dafeiyu/skins/kurumi-animated-v3/`，并写入 `$DSH_HOME/dsh-dafeiyu/skin.json`。`SUCCESS`、摸头、戳击和整理发带只在相应事件触发时播放一次；IDLE、THINKING、WAITING、WORKING 是静态姿态。`SUCCESS` 片段含起势、主体和收势帧，最后回到批准待机图。v2 资源目录保留；已有皮肤选择会先保存为 `skin.json.backup-<timestamp>`。默认 `DSH_HOME` 为 `~/.dsh`；不修改其他插件、频道、模型或凭据，不结束 DSH 进程。

删除或移走 `skin.json` 后重启，可恢复插件原始皮肤；安装器保留的旧选择备份可用于恢复此前的自定义皮肤。

## 检查

```sh
node --test extras/kurumi-skin/install-skin.test.mjs
```

检查仅在自动创建的临时目录中验证路径、备份与 dry-run，不触及真实 DSH 配置。桌宠代码许可证遵循仓库根目录 [LICENSE](../../LICENSE)；生成素材与角色权利说明见上文。
