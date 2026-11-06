# v8 头部桌面预览

此版本把 v8 Blender 头部小样的实际网格接入 macOS 桌宠。头部仍未定稿，没有身体、骨骼或角色动作；左右旋转可以检查真实厚度与侧面。

## 使用

先退出 DSH 或关闭桌宠开关，避免旧进程退出时把旧 renderer 写回。按仓库根目录说明构建并安装 Helper 和狂三皮肤后，运行：

```sh
node scripts/enable-v8-head.mjs --dry-run
node scripts/enable-v8-head.mjs
```

退出并重新打开 DSH，让它启动更新后的 Helper。请通过 DSH 启动器运行桌宠：Helper 需要 DSH 提供标准输入协议，不能单独双击 Helper 应用代替。

- 默认静止，没有持续摆头、漂浮或自动转圈。
- 双击或右键：打开查看菜单。
- 正面、斜侧面、左侧面、右侧面、背面：用 2.4 秒平滑转换，结束保持该视角。
- 慢慢转一圈：8 秒播放一次，结束停住。
- 开启“减少动态”时，视角直接切换。
- 仍可拖动和调整大小；头部模式没有走路或招手菜单。
- 取消“3D 头部小样 v8”可回到原 2D 皮肤。

启用脚本先保存完整 `skin.json` 备份，仅改 `renderer`。它尊重 `DSH_HOME`、`DSH_DAFEIYU_ROOT` 和 `DSH_DAFEIYU_LAYOUT_PATH`；不会读取或更改聊天模型凭据。安装 Helper 也会保留上一个应用包供回退。

## 制作与来源

`export_runtime.py` 从本目录的 `kurumi-head-study.blend` 导出指定头部场景，保留修改器计算后的网格、法线、UV 和反壳轮廓。对照图、平面参考和旧全身模型没有加入运行场景。Blender 的世界坐标 `(x, y, z)` 转为 SceneKit 的 `(x, z, -y)`。

运行包位于 `runtime/`：

- `scene.json`：材质、范围和二进制网格索引。
- `geometry.bin.gz`：发布时无损压缩，构建 Helper 时自动解压为 `geometry.bin`；内容是交错的 Float32 位置、法线、UV，以及 UInt32 三角形索引。
- `face.png`、`hair-albedo.png`：v8 使用的脸部与独立发丝纹理。
- `export-check.json`：源工程校验值与导出统计。

重新生成示例：

```sh
blender -b assets/kurumi3d/v8/kurumi-head-study.blend \
  --python assets/kurumi3d/v8/export_runtime.py
```

原生加载器对二进制范围、顶点、索引和纹理进行验证。材质适配处理了 Blender 与 SceneKit 的 UV 纵向差异，并在实际 Metal 渲染中检查 shader 编译失败的洋红输出。原生渲染与 Blender 的灯光、色彩管理不同，因此不宣称画面逐像素一致。

本次新增的是导出、原生加载、视角控制、静止逻辑和安装选择脚本；人物造型和贴图出处仍见 [v8 建模记录](README.md)、[NOTICE](../../../NOTICE.md) 与 [素材条款](../../../ASSET_LICENSE.md)。DSH 桌宠主体归 **QCYTSN 及贡献者**；这不是原项目的新官方模型。

## 检查记录

实际运行包有 104 个网格部分、725,731 个顶点、1,373,408 个三角形。原生检查程序位于 `native/macos/Tests/HeadStudyPreview/main.swift`，在同一 SceneKit 加载器上验证：

- 90 秒没有互动时，姿态不发生变化。
- 显式转圈在 8 秒结束，之后继续保持静止。
- 正面、斜侧面、右侧面、背面均可实际渲染，四个视角无洋红 shader 失败像素。
- 相机取景在不同宽高比和水平旋转中覆盖整个头部。

这些检查只证明运行时加载、材质和查看逻辑可用，并不表示造型已经定稿。
