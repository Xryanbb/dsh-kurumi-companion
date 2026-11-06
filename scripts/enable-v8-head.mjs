#!/usr/bin/env node
// Select the installed, genuine v8 head study without discarding the 2D skin.
import { readFile, writeFile, rename, access, constants } from 'node:fs/promises'
import { homedir } from 'node:os'
import { dirname, join, resolve } from 'node:path'

const args = process.argv.slice(2)
if (args.some(arg => arg !== '--dry-run')) {
  throw new Error('Usage: node scripts/enable-v8-head.mjs [--dry-run]')
}
const dshHome = resolve(process.env.DSH_HOME || join(homedir(), '.dsh'))
const pluginRoot = resolve(process.env.DSH_DAFEIYU_ROOT || join(dshHome, 'profiles/web/node_modules/dsh-dafeiyu'))
const runtime = join(pluginRoot, 'runtime/bin/darwin/dsh-dafeiyu-helper.app/Contents/Resources/assets/kurumi3d/v8/runtime')
const model = JSON.parse(await readFile(join(runtime, 'scene.json'), 'utf8'))
if (model.model !== 'kurumi-head-v8' || model.version !== 1 || !model.meshes?.length) {
  throw new Error('Install the Helper with the v8 runtime package before selecting it.')
}
for (const filename of ['geometry.bin', 'face.png', 'hair-albedo.png']) {
  await access(join(runtime, filename), constants.R_OK)
}
const selectionDirectory = process.env.DSH_DAFEIYU_LAYOUT_PATH
  ? dirname(resolve(process.env.DSH_DAFEIYU_LAYOUT_PATH))
  : join(dshHome, 'dsh-dafeiyu')
const selectionPath = join(selectionDirectory, 'skin.json')
const original = await readFile(selectionPath)
const selection = JSON.parse(original.toString('utf8'))
if (!selection.imagePath) throw new Error('An existing custom skin is required for the 2D fallback.')
await access(selection.imagePath, constants.R_OK)
if (selection.renderer === 'scene3d') {
  console.log(JSON.stringify({ selected: 'kurumi-head-v8', changed: false, selectionPath }))
} else if (args.includes('--dry-run')) {
  console.log(JSON.stringify({ selected: 'kurumi-head-v8', dryRun: true, selectionPath, runtime }))
} else {
  const stamp = new Date().toISOString().replaceAll(':', '-')
  const backup = `${selectionPath}.before-v8-${stamp}`
  const staged = `${selectionPath}.v8-next-${process.pid}`
  await writeFile(backup, original, { flag: 'wx', mode: 0o600 })
  selection.renderer = 'scene3d'
  await writeFile(staged, JSON.stringify(selection, null, 2) + '\n', { flag: 'wx', mode: 0o600 })
  await rename(staged, selectionPath)
  console.log(JSON.stringify({ selected: 'kurumi-head-v8', changed: true, selectionPath, backup }))
}
