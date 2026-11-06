# Notices and attribution

## DSH desktop pet code

The macOS Helper and animation-state integration are derived from components in [QCYTSN/dsh-dafeiyu](https://github.com/QCYTSN/dsh-dafeiyu), Copyright © 2026 QCYTSN and contributors, licensed under MIT. The original authors retain credit for the DSH pet, plugin features, and design. This project adds Kurumi skin loading, event-triggered one-shot frame playback, reduced-motion handling, installation scripts, and a separate editable Kurumi 3D model.

## Windows action reference

Action categories and interaction timing are informed by [DaFeiYu-Desktop-Pet](https://github.com/dsqrwym/DaFeiYu-Desktop-Pet), Copyright © 2026 dsqrwym and FeiYu contributors. Its source code and media have separate notices. This project reuses the platform-independent action ideas only; it does not include that repository's character frames or mask media.

The keyframe production workflow was informed by [PC2005-cloud/dsh-pet](https://github.com/PC2005-cloud/dsh-pet). No images, prompt text, or processing scripts from that repository are included.

## Kurumi artwork

Tokisaki Kurumi is from *Date A Live*. Character rights belong to their respective rights holders. The images here are generated, unofficial fan art and are not endorsed by the official rights holders. See [ASSET_LICENSE.md](ASSET_LICENSE.md).

## v8 head study additions

The v8 head geometry, facial UV calibration, layered hair, bonnet, ribbon loops, review scene, and build scripts were created for this companion project with Codex assistance. No external downloadable base model was used. The study reuses the project’s approved 2D reference and existing v2 face texture; its dedicated hair albedo was generated using OpenAI imagegen. See [v8 provenance and the complete texture prompt](assets/kurumi3d/v8/README.md). These additions do not claim authorship of the Kurumi character or the upstream DSH project.

## Native v8 runtime additions

The evaluated-mesh exporter, SceneKit model loader, head-study view controls, renderer-selection script, and native rendering checks are additional implementation work in this companion project. The runtime mesh and textures derive from the v8 study described above; this does not imply ownership of the character or upstream DSH code.
