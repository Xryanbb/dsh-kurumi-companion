# DSH Kurumi Desktop Pet for macOS

This is a separately maintained Kurumi add-on repository; it is not a GitHub fork. It connects Kurumi's transparent animation frames to the DSH BigFish plugin's state protocol and native macOS Helper. Install the upstream [QCYTSN/dsh-dafeiyu](https://github.com/QCYTSN/dsh-dafeiyu) separately. Its authors retain credit for the original project code and features.

The pet stays still at idle. A click or DSH status event plays one action once, then returns to idle. The old idle, thinking, and working loops no longer autoplay. DSH's Reduced Motion setting freezes ambient loops while preserving click and status-triggered one-shots. The current artwork is still a sparse transparent key-pose sequence, not a complete 24 fps video; it will be replaced with higher-frame-rate clips when Runway Free generation is available again. Kurumi has no animal tail; touching the hair-accessory area plays the ribbon-adjustment response.

| Idle | Thinking / waiting |
| --- | --- |
| ![Kurumi idle](extras/kurumi-animation/generated/kurumi-idle-preview.gif) | ![Kurumi thinking](extras/kurumi-animation/generated/kurumi-thinking-preview.gif) |

| Reading / working | Happy greeting |
| --- | --- |
| ![Kurumi working](extras/kurumi-animation/generated/kurumi-working-preview.gif) | ![Kurumi greeting](extras/kurumi-animation/generated/kurumi-wave-preview.gif) |

| New staged greeting (anticipation → wave → return to idle) |
| --- |
| ![Kurumi staged greeting](extras/kurumi-animation/generated/kurumi-wave-v2-preview.gif) |

| Head-pat response | Poke response | Hair-ribbon response |
| --- | --- | --- |
| ![Kurumi head-pat](extras/kurumi-animation/generated/kurumi-head-pat-preview.gif) | ![Kurumi poke](extras/kurumi-animation/generated/kurumi-poke-preview.gif) | ![Kurumi ribbon](extras/kurumi-animation/generated/kurumi-hair-ribbon-preview.gif) |

These GIFs are production examples; some still show the older looped frames. They do not represent the current still-idle setting or finished 24 fps clips. See the [Windows action mapping](extras/kurumi-animation/windows-action-port.md), [prompt set](extras/kurumi-animation/generated/wave-prompt-v3.md), and [NOTICE](NOTICE.md) for scope and attribution.

## Install

Requires macOS 12+, Node.js, and Xcode Command Line Tools. Fully quit the DSH Host, then run from this repository root:

```sh
export DSH_DAFEIYU_ROOT="$HOME/.dsh/profiles/web/node_modules/dsh-dafeiyu"

native/macos/build-helper.sh
scripts/install-helper.sh
node extras/kurumi-skin/install-skin.mjs --dry-run
node extras/kurumi-skin/install-skin.mjs
```

Restart DSH to apply. The installer backs up the previous Helper under `~/.dsh/dsh-dafeiyu/backups/` and saves the previous `skin.json`; older skin folders remain available. The scripts do not stop DSH or read or change model credentials.

To roll back, quit DSH, move the backed-up Helper back into the plugin directory, restore the `skin.json` backup, and restart.

## Scope

- The DSH BigFish plugin provides session events; this project supplies the macOS Helper adaptation and Kurumi skin.
- Helper code is derived from the original DSH desktop pet. This repository does not copy BigFish character frames.
- This is a transparent keyframe solution, not Live2D or the Windows version's 100-clip library.
- Tokisaki Kurumi is a character from *Date A Live*. The pictures are unofficial fan art; see [ASSET_LICENSE.md](ASSET_LICENSE.md).
- Autoplay loops are disabled. Click responses still use the older sparse key-pose sequences; replacing them with 24 fps transparent clips is not complete yet.

## Sources

Original project: **QCYTSN and contributors**, [dsh-dafeiyu](https://github.com/QCYTSN/dsh-dafeiyu). Windows action categories and interaction timing reference **dsqrwym and FeiYu contributors**, [DaFeiYu-Desktop-Pet](https://github.com/dsqrwym/DaFeiYu-Desktop-Pet); no BigFish character frames are included.
